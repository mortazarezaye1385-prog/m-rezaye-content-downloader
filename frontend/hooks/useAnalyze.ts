"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { isAbortError, toErrorBody } from "@/lib/api";
import type { ApiErrorBody } from "@/types/api";

export type AnalyzeStatus = "idle" | "analyzing" | "success" | "error";

export interface AnalyzeState<T> {
  status: AnalyzeStatus;
  data: T | null;
  error: ApiErrorBody | null;
  lastUrl: string | null;
}

/** Runs one analysis at a time; a new run aborts the previous request. */
export function useAnalyze<T>(fn: (url: string, signal: AbortSignal) => Promise<T>) {
  const [state, setState] = useState<AnalyzeState<T>>({ status: "idle", data: null, error: null, lastUrl: null });
  const controller = useRef<AbortController | null>(null);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => () => controller.current?.abort(), []);

  const run = useCallback(async (url: string) => {
    controller.current?.abort();
    const current = new AbortController();
    controller.current = current;
    setState({ status: "analyzing", data: null, error: null, lastUrl: url });
    try {
      const data = await fnRef.current(url, current.signal);
      if (!current.signal.aborted) setState({ status: "success", data, error: null, lastUrl: url });
    } catch (error) {
      if (isAbortError(error) || current.signal.aborted) return;
      setState({ status: "error", data: null, error: toErrorBody(error), lastUrl: url });
    }
  }, []);

  const fail = useCallback((error: ApiErrorBody, url: string | null = null) => {
    controller.current?.abort();
    setState({ status: "error", data: null, error, lastUrl: url });
  }, []);

  const reset = useCallback(() => {
    controller.current?.abort();
    setState({ status: "idle", data: null, error: null, lastUrl: null });
  }, []);

  return { ...state, run, fail, reset };
}
