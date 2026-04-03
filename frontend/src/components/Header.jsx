import React from "react";
import { AppBar, Toolbar, Typography } from "@mui/material";
import ImageSearchIcon from "@mui/icons-material/ImageSearch";

export default function Header() {
  return (
    <AppBar position="static" sx={{ bgcolor: "#00695c" }}>
      <Toolbar>
        <ImageSearchIcon sx={{ mr: 1 }} />
        <Typography variant="h6" fontWeight="bold">Visual Image Search Engine</Typography>
      </Toolbar>
    </AppBar>
  );
}
