// frontend/src/api/osint.ts

import { API_BASE_URL } from "./config";

export interface CrawlJob {
  id: number;
  platform: string;
  query: string;
  schedule?: string;
  status: string;
  created_at: string;
  completed_at?: string;
}

export interface SocialPost {
  id: number;
  platform: string;
  post_id: string;
  content: {
    text?: string;
    title?: string;
    hashtags?: string[];
  };
  timestamp: string;
  author_hash: string;
  url?: string;
}

export interface MisinformationEvent {
  id: number;
  post_id: number;
  claim_text: string;
  fact_check_url?: string;
  confidence: number;
  detected_at: string;
}

export const startCrawl = async (platform: string, query: string): Promise<CrawlJob> => {
  const response = await fetch(`${API_BASE_URL}/osint/crawl`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ platform, query }),
  });
  if (!response.ok) {
    throw new Error("Failed to start crawl job");
  }
  return response.json();
};

export const getJobStatus = async (jobId: number): Promise<CrawlJob> => {
  const response = await fetch(`${API_BASE_URL}/osint/job/${jobId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch job status");
  }
  return response.json();
};

export const fetchNetwork = async (platform?: string) => {
  const url = platform ? `${API_BASE_URL}/osint/network?platform=${platform}` : `${API_BASE_URL}/osint/network`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error("Failed to fetch actor network");
  }
  return response.json();
};

export const fetchMisinformation = async (): Promise<MisinformationEvent[]> => {
  const response = await fetch(`${API_BASE_URL}/osint/misinformation`);
  if (!response.ok) {
    throw new Error("Failed to fetch misinformation events");
  }
  return response.json();
};

export const fetchSummary = async (query: string): Promise<{ summary: string }> => {
  const response = await fetch(`${API_BASE_URL}/osint/summary/${encodeURIComponent(query)}`);
  if (!response.ok) {
    throw new Error("Failed to fetch AI summary");
  }
  return response.json();
};
