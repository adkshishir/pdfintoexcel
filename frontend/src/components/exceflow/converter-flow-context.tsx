'use client';

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';

type ConverterFlowContextValue = {
  openFilePicker: () => void;
  registerFileInput: (el: HTMLInputElement | null) => void;
  registerRequestUploadStep: (fn: (() => void) | null) => void;
  /** True once user has a file — hero marketing column hides. */
  heroFocused: boolean;
  setHeroFocused: (focused: boolean) => void;
};

const ConverterFlowContext = createContext<ConverterFlowContextValue | null>(
  null,
);

export function ConverterFlowProvider({ children }: { children: ReactNode }) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const goUploadRef = useRef<(() => void) | null>(null);
  const [heroFocused, setHeroFocused] = useState(false);

  const registerFileInput = useCallback((el: HTMLInputElement | null) => {
    inputRef.current = el;
  }, []);

  const registerRequestUploadStep = useCallback((fn: (() => void) | null) => {
    goUploadRef.current = fn;
  }, []);

  const openFilePicker = useCallback(() => {
    document.getElementById('converter')?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    });
    goUploadRef.current?.();
    requestAnimationFrame(() => inputRef.current?.click());
  }, []);

  const value = useMemo(
    () => ({
      openFilePicker,
      registerFileInput,
      registerRequestUploadStep,
      heroFocused,
      setHeroFocused,
    }),
    [openFilePicker, registerFileInput, registerRequestUploadStep, heroFocused],
  );

  return (
    <ConverterFlowContext.Provider value={value}>
      {children}
    </ConverterFlowContext.Provider>
  );
}

export function useConverterFlow() {
  const ctx = useContext(ConverterFlowContext);
  if (!ctx) {
    throw new Error('useConverterFlow must be used within ConverterFlowProvider');
  }
  return ctx;
}
