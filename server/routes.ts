import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertExpertSchema, insertConversationSchema, insertMessageSchema } from "@shared/schema";
import { chat } from "./anthropic";
import { z } from "zod";

const pythonExpertRoutes = new Set(['auto-clone', 'auto-clone-stream', 'auto-clone-status', 'test-chat']);

export async function registerRoutes(app: Express): Promise<Server> {
  // Get all experts
  app.get("/api/experts", async (req, res) => {
    try {
      const experts = await storage.getExperts();
      res.json(experts);
    } catch (error) {
      console.error("Error fetching experts:", error);
      res.status(500).json({ error: "Failed to fetch experts" });
    }
  });

  // Get single expert
  app.get("/api/experts/:id", async (req, res, next) => {
    if (pythonExpertRoutes.has(req.params.id)) {
      return next();
    }
    try {
      const expert = await storage.getExpert(req.params.id);
      if (!expert) {
        return res.status(404).json({ error: "Expert not found" });
      }
      res.json(expert);
    } catch (error) {
      console.error("Error fetching expert:", error);
      res.status(500).json({ error: "Failed to fetch expert" });
    }
  });

  // Create expert
  app.post("/api/experts", async (req, res) => {
    try {
      const data = insertExpertSchema.parse(req.body);
      const expert = await storage.createExpert(data);
      res.status(201).json(expert);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ error: error.errors });
      }
      console.error("Error creating expert:", error);
      res.status(500).json({ error: "Failed to create expert" });
    }
  });

  // REMOVED: All conversation/message routes now proxied to Python backend
  // This ensures seed experts work correctly via get_expert_by_id()
  
  // // Get conversations for an expert
  // app.get("/api/conversations", async (req, res) => {
  //   try {
  //     const expertId = req.query.expertId as string | undefined;
  //     const conversations = await storage.getConversations(expertId);
  //     res.json(conversations);
  //   } catch (error) {
  //     console.error("Error fetching conversations:", error);
  //     res.status(500).json({ error: "Failed to fetch conversations" });
  //   }
  // });

  // // Get single conversation
  // app.get("/api/conversations/:id", async (req, res) => {
  //   try {
  //     const conversation = await storage.getConversation(req.params.id);
  //     if (!conversation) {
  //       return res.status(404).json({ error: "Conversation not found" });
  //     }
  //     res.json(conversation);
  //   } catch (error) {
  //     console.error("Error fetching conversation:", error);
  //     res.status(500).json({ error: "Failed to fetch conversation" });
  //   }
  // });

  // // Create conversation
  // app.post("/api/conversations", async (req, res) => {
  //   try {
  //     const data = insertConversationSchema.parse(req.body);
  //     const conversation = await storage.createConversation(data);
  //     res.status(201).json(conversation);
  //   } catch (error) {
  //     if (error instanceof z.ZodError) {
  //       return res.status(400).json({ error: error.errors });
  //     }
  //     console.error("Error creating conversation:", error);
  //     res.status(500).json({ error: "Failed to create conversation" });
  //   }
  // });

  // // Get messages for a conversation
  // app.get("/api/conversations/:id/messages", async (req, res) => {
  //   try {
  //     const messages = await storage.getMessages(req.params.id);
  //     res.json(messages);
  //   } catch (error) {
  //     console.error("Error fetching messages:", error);
  //     res.status(500).json({ error: "Failed to fetch messages" });
  //   }
  // });

  // // Send message and get AI response
  // app.post("/api/conversations/:id/messages", async (req, res) => {
  //   try {
  //     const conversationId = req.params.id;
  //     
  //     // Validate message payload with Zod
  //     const messageSchema = z.object({
  //       content: z.string().min(1, "Message content is required"),
  //     });
  //     
  //     const { content } = messageSchema.parse(req.body);

  //     const conversation = await storage.getConversation(conversationId);
  //     if (!conversation) {
  //       return res.status(404).json({ error: "Conversation not found" });
  //     }

  //     const expert = await storage.getExpert(conversation.expertId);
  //     if (!expert) {
  //       return res.status(404).json({ error: "Expert not found" });
  //     }

  //     // Save user message
  //     const userMessage = await storage.createMessage({
  //       conversationId,
  //       role: "user",
  //       content,
  //     });

  //     // Get conversation history
  //     const allMessages = await storage.getMessages(conversationId);
  //     const history = allMessages
  //       .filter(m => m.id !== userMessage.id)
  //       .map(m => ({
  //         role: m.role as "user" | "assistant",
  //         content: m.content,
  //       }));

  //     // Get AI response
  //     const aiResponse = await chat(
  //       expert.systemPrompt,
  //       [...history, { role: "user", content }]
  //     );

  //     // Save AI message
  //     const assistantMessage = await storage.createMessage({
  //       conversationId,
  //       role: "assistant",
  //       content: aiResponse,
  //     });

  //     res.status(201).json({
  //       userMessage,
  //       assistantMessage,
  //     });
  //   } catch (error) {
  //     if (error instanceof z.ZodError) {
  //       return res.status(400).json({ error: error.errors });
  //     }
  //     console.error("Error processing message:", error);
  //     res.status(500).json({ error: "Failed to process message" });
  //   }
  // });

  const httpServer = createServer(app);
  return httpServer;
}
