from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Import routes
from app.routes import supplychain
from app.routes import insider_shield
from app.routes import osint
from app.routes import responseforge
from app.routes import hardwareforensix
from app.routes import training
from app.routes import evolvoai
from app.routes import collabguard
from app.routes import redteam
from app.routes import ransomguard
from app.routes import cloudforensix
from app.routes import quantumsafe
from app.routes import netguard
from app.routes import ethicsforge
from app.routes import resilientforge
from app.routes import swarmforge
from app.routes import neuroguard
from app.routes import spaceguard
from app.routes import climateshield
from app.routes import nanoquantum
from app.routes import innovateguard
from app.routes import metaforge
from app.routes import droneguard
from app.routes import metaguard
from app.routes import finguard
from app.routes import humanforge
from app.routes import gridshield
from app.routes import promptdefender
from app.routes import globaljurix
from app.routes import zerotrustforge
from app.routes import omnisimulator
from app.routes import audioforensix
from app.routes import visualforensix
from app.routes import biothreatforge
from app.routes import autoguard
from app.routes import electguard
from app.routes import archiveforge
from app.routes import ecoguard
from app.routes import protectforge
from app.routes import ipshield
from app.routes import healthguard
from app.routes import cryptoforge
from app.routes import maritimeguard
from app.routes import aviguard
from app.routes import apthunter
from app.routes import risknova, insureguard
from app.routes import campaignguard
from app.routes import llm_routes
from app.routes import commforensix
from app.routes import modeldefender
from app.routes import firmwareguard
from app.routes import psyopsforge
from app.routes import correlix
from app.routes import collabspace
from app.routes import learnforge
from app.routes import behavix
from app.routes import undergroundforge
from app.routes import zerodayforge
from app.routes import linguaguard
from app.routes import anomalymaster
from app.routes import voiceguard
from app.routes import smartcityguard
from app.routes import defiguard
from app.routes import adversarydefender
from app.routes import sovereignguard
from app.routes import legacyshield

app = FastAPI(title="Amroha01 Security Platform API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(supplychain.router, prefix="/api/supplychain", tags=["supplychain"])
app.include_router(insider_shield.router, prefix="/api/insider_shield", tags=["insider_shield"])
app.include_router(osint.router, prefix="/api/osint", tags=["osint"])
app.include_router(responseforge.router, prefix="/api/responseforge", tags=["responseforge"])
app.include_router(hardwareforensix.router, prefix="/api/hardwareforensix", tags=["hardwareforensix"])
app.include_router(training.router, prefix="/api/training", tags=["training"])
app.include_router(evolvoai.router, prefix="/api/evolvoai", tags=["evolvoai"])
app.include_router(collabguard.router, prefix="/api/collabguard", tags=["collabguard"])
app.include_router(redteam.router, prefix="/api/redteam", tags=["redteam"])
app.include_router(ransomguard.router, prefix="/api/ransomguard", tags=["ransomguard"])
app.include_router(cloudforensix.router, prefix="/api/cloudforensix", tags=["cloudforensix"])
app.include_router(quantumsafe.router, prefix="/api/quantumsafe", tags=["quantumsafe"])
app.include_router(netguard.router, prefix="/api/netguard", tags=["netguard"])
app.include_router(ethicsforge.router, prefix="/api/ethicsforge", tags=["ethicsforge"])
app.include_router(resilientforge.router, prefix="/api/resilientforge", tags=["resilientforge"])
app.include_router(swarmforge.router, prefix="/api/swarmforge", tags=["swarmforge"])
app.include_router(neuroguard.router, prefix="/api/neuroguard", tags=["neuroguard"])
app.include_router(spaceguard.router, prefix="/api/spaceguard", tags=["spaceguard"])
app.include_router(climateshield.router, prefix="/api/climateshield", tags=["climateshield"])
app.include_router(nanoquantum.router, prefix="/api/nanoquantum", tags=["nanoquantum"])
app.include_router(innovateguard.router, prefix="/api/innovateguard", tags=["innovateguard"])
app.include_router(metaforge.router, prefix="/api/metaforge", tags=["metaforge"])
app.include_router(droneguard.router, prefix="/api/droneguard", tags=["droneguard"])
app.include_router(metaguard.router, prefix="/api/metaguard", tags=["metaguard"])
app.include_router(finguard.router, prefix="/api/finguard", tags=["finguard"])
app.include_router(humanforge.router, prefix="/api/humanforge", tags=["humanforge"])
app.include_router(gridshield.router, prefix="/api/gridshield", tags=["gridshield"])
app.include_router(promptdefender.router, prefix="/api/promptdefender", tags=["promptdefender"])
app.include_router(globaljurix.router, prefix="/api/globaljurix", tags=["globaljurix"])
app.include_router(zerotrustforge.router, prefix="/api/zerotrustforge", tags=["zerotrustforge"])
app.include_router(omnisimulator.router, prefix="/api/omnisimulator", tags=["omnisimulator"])
app.include_router(audioforensix.router, prefix="/api/audioforensix", tags=["audioforensix"])
app.include_router(visualforensix.router, prefix="/api/visualforensix", tags=["visualforensix"])
app.include_router(biothreatforge.router, prefix="/api/biothreatforge", tags=["biothreatforge"])
app.include_router(electguard.router, prefix="/api/electguard", tags=["electguard"])
app.include_router(archiveforge.router, prefix="/api/archiveforge", tags=["archiveforge"])
app.include_router(ecoguard.router, prefix="/api/ecoguard", tags=["ecoguard"])
app.include_router(protectforge.router, prefix="/api/protectforge", tags=["protectforge"])
app.include_router(ipshield.router, prefix="/api/ipshield", tags=["ipshield"])
app.include_router(healthguard.router, prefix="/api/healthguard", tags=["healthguard"])
app.include_router(cryptoforge.router, prefix="/api/cryptoforge", tags=["cryptoforge"])
app.include_router(maritimeguard.router, prefix="/api/maritimeguard", tags=["maritimeguard"])
app.include_router(aviguard.router, prefix="/api/aviguard", tags=["aviguard"])
app.include_router(apthunter.router, prefix="/api/apthunter", tags=["apthunter"])
app.include_router(risknova.router, prefix="/api/risknova", tags=["risknova"])
app.include_router(insureguard.router, prefix="/api/insureguard", tags=["InsureGuard"])
app.include_router(campaignguard.router, prefix="/api/campaignguard", tags=["campaignguard"])
app.include_router(commforensix.router, prefix="/api/commforensix", tags=["commforensix"])
app.include_router(modeldefender.router, prefix="/api/modeldefender", tags=["ModelDefender"])
app.include_router(firmwareguard.router, prefix="/api/firmwareguard", tags=["FirmwareGuard"])
app.include_router(psyopsforge.router, prefix="/api/psyopsforge", tags=["PsyOpsForge"])
app.include_router(correlix.router, prefix="/api/correlix", tags=["Correlix"])
app.include_router(collabspace.router, prefix="/api/collabspace", tags=["CollabSpace"])
app.include_router(learnforge.router, prefix="/api/learnforge", tags=["LearnForge"])
app.include_router(behavix.router, prefix="/api/behavix", tags=["Behavix"])
app.include_router(undergroundforge.router, prefix="/api/undergroundforge", tags=["UndergroundForge"])
app.include_router(zerodayforge.router, prefix="/api/zerodayforge", tags=["ZeroDayForge"])
app.include_router(linguaguard.router, prefix="/api/linguaguard", tags=["LinguaGuard"])
app.include_router(anomalymaster.router, prefix="/api/anomalymaster", tags=["AnomalyMaster"])
app.include_router(voiceguard.router, prefix="/api/voiceguard", tags=["VoiceGuard"])
app.include_router(smartcityguard.router, prefix="/api/smartcityguard", tags=["SmartCityGuard"])
app.include_router(defiguard.router, prefix="/api/defiguard", tags=["DeFiGuard"])
app.include_router(adversarydefender.router, prefix="/api/adversarydefender", tags=["AdversaryDefender"])
app.include_router(sovereignguard.router, prefix="/api/sovereignguard", tags=["SovereignGuard"])
app.include_router(legacyshield.router, prefix="/api/legacyshield", tags=["LegacyShield"])
# LLM Routes do not have a prefix because they map directly to /api/chat and /api/sentinel
app.include_router(llm_routes.router, tags=["sentinel-llm"])

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "modules_loaded": [
        "supplychain", "insider_shield", "osint", "responseforge", "hardwareforensix", "training", "evolvoai", "collabguard", "redteam", "ransomguard", "cloudforensix", "quantumsafe", "netguard", "ethicsforge", "resilientforge", "swarmforge", "neuroguard", "spaceguard", "climateshield", "nanoquantum", "innovateguard", "metaforge", "droneguard", "metaguard", "finguard", "humanforge", "gridshield", "promptdefender", "globaljurix", "zerotrustforge", "omnisimulator", "audioforensix", "visualforensix", "biothreatforge", "apthunter", "risknova", "campaignguard"
    ]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
