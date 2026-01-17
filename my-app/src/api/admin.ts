import client from "./client";

export const fetchSearchFeedback = (status = "pending") =>
  client.get("/api/admin/search-feedback", { params: { status } });

export const approveSearchFeedback = (id: string) =>
  client.post(`/api/admin/search-feedback/${id}/approve`);

export const rejectSearchFeedback = (id: string, reason?: string) =>
  client.post(`/api/admin/search-feedback/${id}/reject`, { reason });

export const fetchAdminInsights = () => client.get("/api/admin/insights");
