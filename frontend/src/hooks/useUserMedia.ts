/*
  Reusable user-media hook with global caching and reference counting.
  - Avoids React StrictMode double-mount races by keeping the stream alive
    for a short grace period when the last consumer unmounts
  - Reuses the same stream across components to prevent repeated permission prompts
*/
import { useEffect, useRef, useState } from 'react';

type UseUserMediaResult = {
  stream: MediaStream | null;
  error: Error | null;
  isPending: boolean;
  release: () => void;
};

type CacheEntry = {
  promise: Promise<MediaStream> | null;
  stream: MediaStream | null;
  consumers: number;
  stopTimer: any | null;
};

const GLOBAL_KEY = '__smart_user_media_cache__';

function getCache(): CacheEntry {
  const w = window as any;
  if (!w[GLOBAL_KEY]) {
    w[GLOBAL_KEY] = { promise: null, stream: null, consumers: 0, stopTimer: null } as CacheEntry;
  }
  return w[GLOBAL_KEY] as CacheEntry;
}

async function getOrCreateStream(constraints: MediaStreamConstraints): Promise<MediaStream> {
  const cache = getCache();
  if (cache.stream) return cache.stream;
  if (!cache.promise) {
    cache.promise = navigator.mediaDevices.getUserMedia(constraints)
      .then((s) => {
        cache.stream = s;
        return s;
      })
      .finally(() => {
        // Clear promise after resolution so re-acquire can happen with new constraints later
        cache.promise = null;
      });
  }
  return cache.promise;
}

function addConsumer() {
  const cache = getCache();
  cache.consumers += 1;
  if (cache.stopTimer) {
    clearTimeout(cache.stopTimer);
    cache.stopTimer = null;
  }
}

function scheduleRelease() {
  const cache = getCache();
  cache.consumers = Math.max(0, cache.consumers - 1);
  if (cache.consumers === 0) {
    // Delay stop slightly to survive StrictMode test unmount/remount
    cache.stopTimer = setTimeout(() => {
      if (cache.consumers === 0 && cache.stream) {
        try { cache.stream.getTracks().forEach((t) => t.stop()); } catch {}
        cache.stream = null;
      }
      cache.stopTimer = null;
    }, 1500);
  }
}

export function releaseAllUserMedia(): void {
  const cache = getCache();
  if (cache.stopTimer) {
    clearTimeout(cache.stopTimer);
    cache.stopTimer = null;
  }
  if (cache.stream) {
    try { cache.stream.getTracks().forEach((t) => t.stop()); } catch {}
  }
  cache.stream = null;
  cache.promise = null;
  cache.consumers = 0;
}

export function useUserMedia(constraints: MediaStreamConstraints, restartKey = 0): UseUserMediaResult {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isPending, setIsPending] = useState<boolean>(true);
  const mountedRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    mountedRef.current = true;
    setIsPending(true);
    setError(null);
    addConsumer();
    getOrCreateStream(constraints)
      .then((s) => {
        if (cancelled) return;
        setStream(s);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e instanceof Error ? e : new Error(String(e)));
      })
      .finally(() => {
        if (!cancelled) setIsPending(false);
      });

    return () => {
      cancelled = true;
      mountedRef.current = false;
      scheduleRelease();
      setStream(null);
    };
  }, [JSON.stringify(constraints), restartKey]);

  const release = () => scheduleRelease();

  return { stream, error, isPending, release };
}


