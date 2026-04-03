import React, { useState, useRef, useCallback } from "react";
import {
  Box, Button, Card, CardMedia, CardContent, CircularProgress, Grid, Paper,
  Stack, Typography, Alert, Chip, Tabs, Tab,
} from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import SearchIcon from "@mui/icons-material/Search";
import AddPhotoAlternateIcon from "@mui/icons-material/AddPhotoAlternate";
import { indexImage, searchImages } from "../services/searchApi";

export default function SearchPage() {
  const [tab, setTab] = useState(0);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);
  const fileRef = useRef(null);

  const handleFile = useCallback((file) => {
    if (!file) return;
    setError(null); setResult(null);
    fileRef.current = file;
    setPreview(URL.createObjectURL(file));
  }, []);

  const handleAction = async () => {
    if (!fileRef.current) return;
    setLoading(true); setError(null);
    try {
      const fd = new FormData();
      fd.append("file", fileRef.current);
      const { data } = tab === 0 ? await indexImage(fd) : await searchImages(fd);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Operation failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={5}>
        <Paper elevation={3} sx={{ p: 3 }}>
          <Tabs value={tab} onChange={(_, v) => { setTab(v); setResult(null); setError(null); }} sx={{ mb: 2 }}>
            <Tab label="Index Image" icon={<AddPhotoAlternateIcon />} iconPosition="start" />
            <Tab label="Search" icon={<SearchIcon />} iconPosition="start" />
          </Tabs>
          <Box
            onClick={() => inputRef.current?.click()}
            sx={{
              border: "2px dashed", borderColor: "grey.400", borderRadius: 2, p: 4,
              textAlign: "center", cursor: "pointer", bgcolor: "grey.50", minHeight: 140,
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
            }}
          >
            <CloudUploadIcon sx={{ fontSize: 48, color: "primary.main", mb: 1 }} />
            <Typography variant="body1" fontWeight={500}>Click to upload image</Typography>
            <Typography variant="caption" color="text.disabled" mt={1}>JPG, PNG, BMP, WebP</Typography>
          </Box>
          <input ref={inputRef} type="file" accept="image/*" style={{ display: "none" }} onChange={(e) => handleFile(e.target.files?.[0])} />
          {preview && (
            <Box mt={2} textAlign="center">
              <img src={preview} alt="preview" style={{ maxWidth: "100%", maxHeight: 180, borderRadius: 8, border: "1px solid #e0e0e0" }} />
            </Box>
          )}
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          <Stack direction="row" spacing={1.5} mt={2}>
            <Button variant="contained" fullWidth onClick={handleAction} disabled={!preview || loading}
              startIcon={loading ? <CircularProgress size={18} color="inherit" /> : (tab === 0 ? <AddPhotoAlternateIcon /> : <SearchIcon />)}>
              {loading ? "Processing…" : (tab === 0 ? "Index Image" : "Search Similar")}
            </Button>
            <Button variant="outlined" onClick={() => { setPreview(null); setResult(null); fileRef.current = null; }} disabled={loading}>Reset</Button>
          </Stack>
        </Paper>
      </Grid>
      <Grid item xs={12} md={7}>
        <Paper elevation={3} sx={{ p: 3, minHeight: 300 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            {tab === 0 ? "Index Result" : "Search Results"}
          </Typography>
          {!result && !loading && (
            <Box display="flex" alignItems="center" justifyContent="center" minHeight={240} color="text.disabled">
              <Typography variant="body2">{tab === 0 ? "Upload and index an image." : "Upload a query image to find similar ones."}</Typography>
            </Box>
          )}
          {loading && (
            <Box display="flex" alignItems="center" justifyContent="center" minHeight={240}>
              <CircularProgress size={48} />
            </Box>
          )}
          {result && !loading && tab === 0 && (
            <Stack spacing={1}>
              <Chip label={`Indexed: ${result.indexed}`} color="success" />
              <Chip label={`Total in index: ${result.total_indexed}`} variant="outlined" />
            </Stack>
          )}
          {result && !loading && tab === 1 && (
            <>
              {result.message && <Alert severity="info">{result.message}</Alert>}
              <Grid container spacing={2} mt={0}>
                {(result.results || []).map((item, i) => (
                  <Grid item xs={6} sm={4} key={i}>
                    <Card variant="outlined">
                      <CardMedia component="img" height="100"
                        image={`data:image/jpeg;base64,${item.thumbnail}`} alt={item.name} />
                      <CardContent sx={{ p: 1, "&:last-child": { pb: 1 } }}>
                        <Typography variant="caption" noWrap display="block">{item.name}</Typography>
                        <Typography variant="caption" color="primary">{(item.similarity * 100).toFixed(1)}% match</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </>
          )}
        </Paper>
      </Grid>
    </Grid>
  );
}
