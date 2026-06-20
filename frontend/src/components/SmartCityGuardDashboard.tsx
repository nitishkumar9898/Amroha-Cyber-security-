import React, { useState, useEffect } from "react";
import axios from "axios";
import "./SmartCityGuardDashboard.css";

export const SmartCityGuardDashboard: React.FC = () => {
  const [events, setEvents] = useState<any[]>([]);
  const [zone, setZone] = useState("");
  const [deviceType, setDeviceType] = useState("");
  const [deviceId, setDeviceId] = useState("");

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = () => {
    axios.get("/api/smartcityguard/events").then(res => setEvents(res.data)).catch(console.error);
  };

  const handleReport = () => {
    axios.post("/api/smartcityguard/events", { city_zone: zone, iot_device_type: deviceType, device_id: deviceId })
      .then(() => {
        fetchEvents();
        setZone(""); setDeviceType(""); setDeviceId("");
      })
      .catch(console.error);
  };

  const handleIsolate = (id: number) => {
    axios.post(`/api/smartcityguard/events/${id}/isolate`)
      .then(() => fetchEvents())
      .catch(console.error);
  };

  return (
    <div className="scg-container">
      <h2>SmartCityGuard Dashboard</h2>
      
      <div className="scg-card">
        <h3>Report IoT Telemetry Event</h3>
        <input placeholder="City Zone (e.g., Downtown Sector A)" value={zone} onChange={e => setZone(e.target.value)} />
        <input placeholder="Device Type (e.g., Traffic Sensor)" value={deviceType} onChange={e => setDeviceType(e.target.value)} />
        <input placeholder="Device ID" value={deviceId} onChange={e => setDeviceId(e.target.value)} />
        <button onClick={handleReport}>Analyze Event</button>
      </div>

      <div className="scg-card">
        <h3>City-Wide Anomaly Events</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Zone</th>
              <th>Device Type</th>
              <th>Device ID</th>
              <th>Anomaly Score</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {events.map(ev => (
              <tr key={ev.id}>
                <td>{ev.id}</td>
                <td>{ev.city_zone}</td>
                <td>{ev.iot_device_type}</td>
                <td>{ev.device_id}</td>
                <td className={ev.anomaly_score > 0.7 ? "critical-score" : ""}>{(ev.anomaly_score * 100).toFixed(1)}%</td>
                <td>{ev.event_status}</td>
                <td>
                  <button className="isolate-btn" onClick={() => handleIsolate(ev.id)} disabled={ev.event_status === "Isolated"}>
                    {ev.event_status === "Isolated" ? "Quarantined" : "Isolate Device"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
