import { getToken } from 'next-auth/jwt';
import dbConnect from '../../../lib/dbConnect';
import Chat from '../../../models/Chat';

export default async function handler(req, res) {
  // Get the JWT token
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });

  // If no token, return Unauthorized
  if (!token) {
    return res.status(401).json({ message: 'Not authenticated' });
  }

  await dbConnect(); // Ensure DB connection

  if (req.method === 'GET') {
    try {
      // Fetch all chats for the authenticated user (sorted by createdAt)
      const chats = await Chat.find({ userId: token.id }).sort({ createdAt: -1 });

      // Group chats by date
      const groupedChats = chats.reduce((acc, chat) => {
        const date = new Date(chat.createdAt).toLocaleDateString('en-US', {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        });

        if (!acc[date]) {
          acc[date] = [];
        }

        acc[date].push({
          id: chat._id.toString(),
          title: chat.title,
          time: new Date(chat.createdAt).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
          }),
          createdAt: chat.createdAt,
        });

        return acc;
      }, {});

      res.status(200).json(groupedChats);  // Return the grouped chats
    } catch (error) {
      res.status(500).json({ message: 'Failed to fetch chats', error: error.message });  // Internal server error
    }
  } else if (req.method === 'POST') {
    // Handle POST request (creating a new chat)
    try {
      const { title, messages, userId } = req.body;

      const newChat = new Chat({
        userId,
        title,
        messages,
        createdAt: new Date(),
        updatedAt: new Date(),
      });

      const result = await newChat.save();  // Save new chat to DB

      res.status(201).json({
        _id: result._id,
        ...newChat.toObject(),
      });
    } catch (error) {
      res.status(500).json({ message: 'Failed to create chat', error: error.message });  // Internal server error
    }
  } else if (req.method === 'PUT') {
    // Handle PUT request for updating messages in the chat
    try {
      const { messages, title } = req.body;
      const chatId = req.query.id;  // Extract chatId from query parameter

      const chat = await Chat.findById(chatId);
      if (!chat) {
        return res.status(404).json({ message: 'Chat not found' });
      }

      // Update chat with new messages
      chat.messages = messages;
      chat.title = title || chat.title;  // Update title if provided
      chat.updatedAt = new Date();

      await chat.save();  // Save updated chat

      res.status(200).json(chat);  // Return updated chat
    } catch (error) {
      res.status(500).json({ message: 'Failed to update chat', error: error.message });  // Internal server error
    }
  } else {
    res.setHeader('Allow', ['GET', 'POST', 'PUT']);
    res.status(405).json({ message: `Method ${req.method} not allowed` });  // Handle invalid methods
  }
}
