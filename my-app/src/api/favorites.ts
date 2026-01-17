import client from "./client";

export const upsertFavorite = (payload: any) =>
  client.post("/api/favorites", payload);

export const fetchFavorites = () => client.get("/api/me/favorites");
