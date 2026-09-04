import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { TrackRecordResponse } from "../types";

export function useTrackRecord() {
  const [data, setData] = useState<TrackRecordResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    api.getTrackRecord().then((res) => { if (!cancelled) setData(res); }).catch(() => {});
    return () => { cancelled = true; };
  }, []);

  return data;
}
