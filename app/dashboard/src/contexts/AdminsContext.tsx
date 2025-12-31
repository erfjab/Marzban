import { useQuery } from "react-query";
import { fetch } from "service/http";
import { z } from "zod";
import { create } from "zustand";
import { useDashboard } from "./DashboardContext";

export const AdminSchema = z.object({
  username: z.string().min(1, "Username is required"),
  is_sudo: z.boolean(),
  password: z.string().optional(),
  telegram_id: z.union([z.number(), z.string()]).optional().nullable(),
  discord_webhook: z.string().optional().nullable(),
  subscription_title: z.string().optional().nullable(),
  announce: z.string().optional().nullable(),
  announce_url: z.string().optional().nullable(),
  users_usage: z.number().optional().nullable(),
});

export type AdminType = z.infer<typeof AdminSchema>;

export const getAdminDefaultValues = (): AdminType => ({
  username: "",
  is_sudo: false,
  password: "",
  telegram_id: null,
  discord_webhook: null,
  subscription_title: null,
  announce: null,
  announce_url: null,
});

export const FetchAdminsQueryKey = "fetch-admins-query-key";

export type AdminStore = {
  admins: AdminType[];
  addAdmin: (admin: AdminType) => Promise<unknown>;
  fetchAdmins: () => Promise<AdminType[]>;
  updateAdmin: (admin: AdminType) => Promise<unknown>;
  deletingAdmin?: AdminType | null;
  deleteAdmin: () => Promise<unknown>;
  setDeletingAdmin: (admin: AdminType | null) => void;
};

export const useAdminsQuery = () => {
  const { isEditingAdmins } = useDashboard();
  return useQuery({
    queryKey: FetchAdminsQueryKey,
    queryFn: useAdmins.getState().fetchAdmins,
    refetchInterval: isEditingAdmins ? 3000 : undefined,
    refetchOnWindowFocus: false,
  });
};

export const useAdmins = create<AdminStore>((set, get) => ({
  admins: [],
  addAdmin(body) {
    return fetch("/admin", { method: "POST", body });
  },
  fetchAdmins() {
    return fetch("/admins");
  },
  updateAdmin(body) {
    return fetch(`/admin/${body.username}`, {
      method: "PUT",
      body,
    });
  },
  setDeletingAdmin(admin) {
    set({ deletingAdmin: admin });
  },
  deleteAdmin: () => {
    return fetch(`/admin/${get().deletingAdmin?.username}`, {
      method: "DELETE",
    });
  },
}));
