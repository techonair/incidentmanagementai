"use client";

import { create } from "zustand";

type ToastStore = {
  message: string;
  setMessage: (message: string) => void;
};

export const useToast = create<ToastStore>((set) => ({
  message: "",
  setMessage: (message) => set({ message })
}));
