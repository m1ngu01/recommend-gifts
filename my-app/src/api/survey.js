import client from "./client";

export const fetchSurveyPrompt = () => client.get("/api/survey/search-prompt");

export const submitSurveyAnswer = (payload) =>
  client.post("/api/survey/answers", payload);
