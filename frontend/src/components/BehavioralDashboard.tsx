// frontend/src/components/BehavioralDashboard.tsx
import React, { useState, useEffect } from "react";
import axios from "axios";

interface ProfileResult {
  user_id: string;
  social_engineering: { is_social_engineering: boolean; matched_cues: string[] };
  insider_threat_score: number;
  zkp_proof: any;
}

const BehavioralDashboard: React.FC = () => {
  const [userId] = useState("example_user");
  const [profile, setProfile] = useState<ProfileResult | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const footprint = {
        messages: [
          "Urgent! Verify your account now.",
          "Click here to reset password."
        ],
        activities: [
          { type: "access_sensitive_file", detail: "read confidential.docx" },
          { type: "login", detail: "VPN login" }
        ]
      };
      const resp = await axios.post(`/api/behavioral/profile/${userId}`, footprint);
      setProfile(resp.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  return (
    <div style={{ padding: "1rem", background: "#1e1e1e", color: "#e0e0e0" }}>
      <h2>Behavioral Profile Dashboard</h2>
      {loading && <p>Loading...</p>}
      {profile && (
        <div>
          <p><strong>User:</strong> {profile.user_id}</p>
          <p><strong>Social Engineering Detected:</strong> {profile.social_engineering.is_social_engineering ? "Yes" : "No"}</p>
          <p><strong>Matched Cues:</strong> {profile.social_engineering.matched_cues.join(", ")}</p>
          <p><strong>Insider Threat Score:</strong> {profile.insider_threat_score}</p>
        </div>
      )}
    </div>
  );
};

export default BehavioralDashboard;
