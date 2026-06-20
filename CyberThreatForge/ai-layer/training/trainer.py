"""
=============================================================================
CyberThreatForge — AI Training Pipeline
=============================================================================

PyTorch-based continual learning pipeline for all SentinelCore AI models.

Architecture:
  Trainer
  ├── DataModule (loads replay buffer, threat feeds, feedback)
  ├── ModelModule (loads base model + LoRA adapters)
  ├── LossModule (cross-entropy + EWC regularization + contrastive)
  ├── OptimizerModule (AdamW with cosine schedule)
  ├── Evaluator (held-out validation, regression check)
  ├── Logger (MLflow / Weights & Biases)
  └── Checkpointer (versioned snapshots)

Training modes:
  - full: Complete model training (rare, for new models)
  - continual: Incremental fine-tuning with EWC
  - lora: Low-rank adapter training (most common — fast, no forgetting)
  - rlhf: Reinforcement Learning from Human Feedback

Requirements: torch>=2.4, transformers>=4.42, peft>=0.12, bitsandbytes>=0.44

@version 2.0.0
"""

import os
import json
import uuid
import time
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts

# ─── Configuration ──────────────────────────────────────────────────────────

@dataclass
class TrainingConfig:
    """Training configuration — loaded from /config/training.yaml"""
    experiment_name: str = "sentinel-core-v2"
    base_model: str = "microsoft/Phi-3-medium-128k-instruct"
    
    # Continual learning
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    batch_size: int = 4
    gradient_accumulation_steps: int = 8
    max_steps: int = 500
    warmup_steps: int = 50
    lora_rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    
    # EWC (Elastic Weight Consolidation)
    ewc_lambda: float = 0.4  # Regularization strength
    ewc_num_samples: int = 200
    
    # Memory replay
    replay_buffer_size: int = 10000
    replay_batch_ratio: float = 0.3  # 30% replay in each batch
    
    # RLHF
    rlhf_learning_rate: float = 1e-6
    preference_model: str = "reward-model-v1"
    
    # Evaluation
    eval_steps: int = 50
    save_steps: int = 100
    max_grad_norm: float = 1.0
    mixed_precision: str = "bf16"
    
    # Data
    max_seq_length: int = 8192
    domain_weights: Dict[str, float] = field(default_factory=lambda: {
        "malware_analysis": 0.20,
        "deepfake": 0.15,
        "mobile_forensics": 0.10,
        "apt_hunting": 0.15,
        "threat_intel": 0.15,
        "digital_forensics": 0.10,
        "cyber_psychology": 0.05,
        "reporting": 0.05,
        "ai_governance": 0.05,
    })

# ─── Data Module ────────────────────────────────────────────────────────────

class TrainingExample(Dataset):
    """Loads training examples from the replay buffer (PostgreSQL/Parquet)."""
    
    def __init__(self, config: TrainingConfig, mode: str = "train"):
        self.config = config
        self.mode = mode
        self.examples: List[Dict] = []
        self.load_data()
        
    def load_data(self):
        """Fetch examples from PostgreSQL replay buffer or Parquet files."""
        # In production: read from `continual_learning.replay_buffer` table
        # or from S3/Parquet for historical data
        pass
        
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        ex = self.examples[idx]
        return {
            "input_ids": torch.tensor(ex["input_ids"]),
            "attention_mask": torch.tensor(ex["attention_mask"]),
            "labels": torch.tensor(ex["labels"]),
            "domain": ex.get("domain", "general"),
            "weight": ex.get("weight", 1.0),
        }

# ─── EWC Module ─────────────────────────────────────────────────────────────

class ElasticWeightConsolidation:
    """
    Elastic Weight Consolidation — prevents catastrophic forgetting.
    
    EWC loss = Σ (λ/2) * F_i * (θ_i - θ*_i)²
    
    Where:
      - F_i = Fisher Information Matrix diagonal (importance per parameter)
      - λ = regularization strength
      - θ_i = current parameters
      - θ*_i = previous optimal parameters
    """
    
    def __init__(self, model: nn.Module, fisher_samples: int = 200, ewc_lambda: float = 0.4):
        self.model = model
        self.fisher_samples = fisher_samples
        self.ewc_lambda = ewc_lambda
        self.fisher_matrix: Dict[str, torch.Tensor] = {}
        self.optimal_params: Dict[str, torch.Tensor] = {}
        
    def estimate_fisher(self, dataloader: DataLoader, device: torch.device):
        """Compute Fisher Information Matrix diagonal for current task."""
        self.fisher_matrix = {}
        self.optimal_params = {}
        
        # Store current parameters as optimal
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                self.optimal_params[name] = param.data.clone().detach()
                self.fisher_matrix[name] = torch.zeros_like(param.data)
        
        # Compute Fisher information
        self.model.eval()
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            
            self.model.zero_grad()
            outputs = self.model(input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            
            for name, param in self.model.named_parameters():
                if param.grad is not None and name in self.fisher_matrix:
                    self.fisher_matrix[name] += param.grad.data ** 2 / self.fisher_samples
        
        self.model.train()
    
    def compute_ewc_loss(self) -> torch.Tensor:
        """Compute EWC regularization loss."""
        ewc_loss = 0.0
        for name, param in self.model.named_parameters():
            if name in self.fisher_matrix and name in self.optimal_params:
                fisher = self.fisher_matrix[name]
                optimal = self.optimal_params[name]
                ewc_loss += (fisher * (param - optimal) ** 2).sum()
        
        return (self.ewc_lambda / 2) * ewc_loss

# ─── LoRA Adapter Module ─────────────────────────────────────────────────────

class LoRAAdapter(nn.Module):
    """
    Low-Rank Adaptation — fine-tune small adapters per domain.
    
    W' = W + BA where B ∈ R^{d×r}, A ∈ R^{r×k}, r << min(d,k)
    
    During training, only A and B are updated (base model frozen).
    """
    
    def __init__(self, base_model: nn.Module, rank: int = 16, alpha: int = 32, dropout: float = 0.05):
        super().__init__()
        self.base_model = base_model
        self.rank = rank
        self.alpha = alpha
        self.dropout = dropout
        
        # Freeze base model
        for param in self.base_model.parameters():
            param.requires_grad = False
        
        # LoRA adapters are registered per layer by PEFT library
        # Using HuggingFace PEFT under the hood
        self.adapter_weights: Dict[str, nn.Parameter] = nn.ParameterDict()
    
    def forward(self, *args, **kwargs):
        # PEFT handles the forward pass with adapter weights merged
        return self.base_model(*args, **kwargs)
    
    def save_adapter(self, path: str, domain: str):
        """Save LoRA adapter weights for a specific domain."""
        save_path = Path(path) / domain
        save_path.mkdir(parents=True, exist_ok=True)
        torch.save(self.adapter_weights.state_dict(), save_path / "adapter.pt")
        
        config = {
            "rank": self.rank,
            "alpha": self.alpha,
            "dropout": self.dropout,
            "base_model": self.base_model.config._name_or_path,
            "timestamp": datetime.utcnow().isoformat(),
        }
        with open(save_path / "config.json", "w") as f:
            json.dump(config, f, indent=2)
    
    def load_adapter(self, path: str, domain: str):
        """Load LoRA adapter weights for a specific domain."""
        load_path = Path(path) / domain / "adapter.pt"
        if load_path.exists():
            self.adapter_weights.load_state_dict(torch.load(load_path))

# ─── Trainer ─────────────────────────────────────────────────────────────────

class ContinualTrainer:
    """
    Manages the full training lifecycle:
      - Data loading with replay buffer sampling
      - EWC regularization
      - Domain-specific LoRA fine-tuning
      - Evaluation and regression detection
      - Checkpointing and rollback
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger = logging.getLogger("ContinualTrainer")
        
        # Initialize components
        self.model = None  # Loaded via HuggingFace
        self.lora_model = None
        self.ewc = None
        self.optimizer = None
        self.scheduler = None
        
        # Metrics tracking
        self.train_losses: List[float] = []
        self.eval_metrics: List[Dict] = []
        self.best_accuracy = 0.0
        self.regression_count = 0
        
    def initialize_model(self):
        """Load base model and wrap with LoRA."""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import LoraConfig, get_peft_model
        
        # Load base model
        model_name = self.config.base_model
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16 if self.config.mixed_precision == "bf16" else torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Apply LoRA
        lora_config = LoraConfig(
            r=self.config.lora_rank,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj"],
        )
        self.lora_model = get_peft_model(self.model, lora_config)
        self.lora_model.print_trainable_parameters()
        
        # Initialize EWC
        self.ewc = ElasticWeightConsolidation(
            self.lora_model,
            fisher_samples=self.config.ewc_num_samples,
            ewc_lambda=self.config.ewc_lambda,
        )
        
        self.logger.info(f"Model initialized on {self.device}")
    
    def train_continual(self, train_data: TrainingExample, val_data: Optional[TrainingExample] = None):
        """
        Continual learning training loop.
        
        1. Sample from replay buffer + new data
        2. Compute EWC Fisher information from previous task
        3. Train with EWC regularization
        4. Evaluate — check for regression
        5. If regression > threshold, rollback
        """
        if self.lora_model is None:
            self.initialize_model()
        
        # Setup optimizer
        self.optimizer = AdamW(
            self.lora_model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )
        
        # Setup scheduler
        self.scheduler = CosineAnnealingWarmRestarts(
            self.optimizer,
            T_0=self.config.max_steps // 4,
            T_mult=2,
        )
        
        # Data loaders
        train_loader = DataLoader(
            train_data,
            batch_size=self.config.batch_size,
            shuffle=True,
            drop_last=True,
        )
        
        # Estimate Fisher on previous task data
        if self.ewc and len(train_data) > 0:
            self.ewc.estimate_fisher(train_loader, self.device)
        
        # Training loop
        self.lora_model.train()
        global_step = 0
        total_loss = 0.0
        
        for epoch in range(self.config.max_steps // len(train_loader) + 1):
            for batch in train_loader:
                if global_step >= self.config.max_steps:
                    break
                
                # Move to device
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)
                
                # Forward pass
                outputs = self.lora_model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )
                loss = outputs.loss
                
                # EWC regularization
                if self.ewc:
                    ewc_loss = self.ewc.compute_ewc_loss()
                    loss += ewc_loss
                
                # Scale loss for gradient accumulation
                loss = loss / self.config.gradient_accumulation_steps
                loss.backward()
                
                total_loss += loss.item()
                
                if (global_step + 1) % self.config.gradient_accumulation_steps == 0:
                    # Gradient clipping
                    torch.nn.utils.clip_grad_norm_(
                        self.lora_model.parameters(),
                        self.config.max_grad_norm,
                    )
                    
                    self.optimizer.step()
                    self.scheduler.step()
                    self.optimizer.zero_grad()
                
                # Logging
                if global_step % 10 == 0:
                    avg_loss = total_loss / (global_step + 1)
                    self.logger.info(
                        f"Step {global_step}/{self.config.max_steps} | "
                        f"Loss: {avg_loss:.4f} | "
                        f"LR: {self.scheduler.get_last_lr()[0]:.2e}"
                    )
                
                global_step += 1
        
        self.logger.info(f"Training complete. Total steps: {global_step}")
        return {"loss": total_loss / global_step, "steps": global_step}
    
    def evaluate(self, val_data: TrainingExample) -> Dict[str, float]:
        """Evaluate model and check for regression."""
        self.lora_model.eval()
        val_loader = DataLoader(val_data, batch_size=self.config.batch_size)
        
        total_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)
                
                outputs = self.lora_model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )
                total_loss += outputs.loss.item()
                
                # Accuracy computation
                preds = outputs.logits.argmax(dim=-1)
                correct += (preds == labels).sum().item()
                total += labels.numel()
        
        accuracy = correct / max(total, 1)
        avg_loss = total_loss / max(len(val_loader), 1)
        
        metrics = {
            "accuracy": accuracy,
            "loss": avg_loss,
            "perplexity": torch.exp(torch.tensor(avg_loss)).item(),
        }
        
        # Check for regression
        if accuracy < self.best_accuracy - 0.03:
            self.regression_count += 1
            self.logger.warning(
                f"Regression detected! Accuracy: {accuracy:.4f} vs best: {self.best_accuracy:.4f}"
            )
            metrics["regression_detected"] = True
        else:
            self.best_accuracy = max(self.best_accuracy, accuracy)
            metrics["regression_detected"] = False
        
        self.eval_metrics.append(metrics)
        return metrics
    
    def save_checkpoint(self, path: str, domain: str):
        """Save model snapshot with domain-specific adapter."""
        if self.lora_model:
            save_path = Path(path) / f"snapshot-{uuid.uuid4().hex[:8]}"
            self.lora_model.save_pretrained(save_path)
            self.tokenizer.save_pretrained(save_path)
            
            # Save metadata
            metadata = {
                "domain": domain,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": self.eval_metrics[-1] if self.eval_metrics else {},
                "config": asdict(self.config),
            }
            with open(save_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Checkpoint saved: {save_path}")
            return str(save_path)
    
    def load_checkpoint(self, path: str):
        """Load model snapshot for rollback."""
        if self.lora_model:
            self.lora_model.load_adapter(path)
            self.logger.info(f"Checkpoint loaded: {path}")

# ─── Main Entry Point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    config = TrainingConfig()
    trainer = ContinualTrainer(config)
    trainer.initialize_model()
    
    # In production: load from database
    # train_data = TrainingExample(config, mode="train")
    # val_data = TrainingExample(config, mode="val")
    
    # Mock training example
    # metrics = trainer.train_continual(train_data, val_data)
    # eval_results = trainer.evaluate(val_data)
    # trainer.save_checkpoint("/models/snapshots/", "general")
    
    logging.info("Training pipeline initialized — ready for data")
