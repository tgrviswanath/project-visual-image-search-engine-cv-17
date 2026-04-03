import axios from "axios";
const api = axios.create({ baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000" });
export const indexImage = (fd) =>
  api.post("/api/v1/index", fd, { headers: { "Content-Type": "multipart/form-data" } });
export const searchImages = (fd) =>
  api.post("/api/v1/search", fd, { headers: { "Content-Type": "multipart/form-data" } });
