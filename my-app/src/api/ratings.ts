import client from "./client";

export const submitRating = (payload: { product_id: string; rating: number }) =>
  client.post("/api/ratings", payload);

export const fetchRatingSummary = (productId: string) =>
  client.get(`/api/ratings/${encodeURIComponent(productId)}`);
