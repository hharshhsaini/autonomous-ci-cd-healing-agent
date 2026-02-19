import { useState, useEffect, useRef } from "react";

export function useAgentStream(jobId) {
  const [data, setData] = useState(null);
  const [isComplete, setIsComplete] = useState(false);
  const esRef = useRef(null);

  useEffect(() => {
    if (!jobId) return;

    const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
    
    if (esRef.current) esRef.current.close();

    const es = new EventSource(`${API}/api/stream/${jobId}`);
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data);
        setData(parsed);
        
        if (["done", "failed"].includes(parsed.status)) {
          setIsComplete(true);
          es.close();
        }
      } catch (err) {
        console.error("Parse error:", err);
      }
    };

    es.onerror = () => {
      // Browser will auto-retry
    };

    return () => es.close();
  }, [jobId]);

  return { data, isComplete };
}
