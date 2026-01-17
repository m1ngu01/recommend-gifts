// src/components/ChatBotBox.jsx
import { Box, Typography, Paper } from "@mui/material";

export default function ChatBotBox({ sender, message }: any) {
  const isUser = sender === "user";

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        mb: 1,
      }}
    >
      <Paper
        elevation={2}
        sx={{
          p: 1.5,
          maxWidth: "70%",
          backgroundColor: isUser ? "var(--accent)" : "var(--bg-soft)",
          color: isUser ? "#fff" : "var(--fg)",
          borderRadius: 2,
          border: isUser ? "none" : "1px solid var(--border)",
        }}
      >
        <Typography variant="body2">{message}</Typography>
      </Paper>
    </Box>
  );
}

