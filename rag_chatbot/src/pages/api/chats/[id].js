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

  const { id } = req.query; // Extract chat ID from the request query

  // Handle GET request (fetching the chat)
  if (req.method === 'GET') {
    try {
      const chat = await Chat.findOne({
        _id: id,
        userId: token.id, // Ensure the chat belongs to the authenticated user using token
      });

      if (!chat) {
        return res.status(404).json({ error: 'Chat not found' });
      }

      res.status(200).json(chat);  // Return the found chat
    } catch (error) {
      res.status(500).json({ message: 'Failed to fetch chat', error: error.message });  // Internal server error
    }
  } else if (req.method === 'PUT') {
    // Handle PUT request (updating the chat)
    try {
      const { messages, title } = req.body; // Extract messages and title from the request body

      const chat = await Chat.findOneAndUpdate(
        { _id: id, userId: token.id },  // Ensure it's the user's chat
        { messages, title, updatedAt: new Date() },
        { new: true }  // Return the updated chat
      );

      if (!chat) {
        return res.status(404).json({ error: 'Chat not found' });
      }

      res.status(200).json(chat);  // Return the updated chat
    } catch (error) {
      res.status(500).json({ message: 'Error updating chat', error: error.message });  // Internal server error
    }
  } else if (req.method === 'DELETE') {
    // Handle DELETE request (deleting the chat)
    try {
      const chat = await Chat.findOneAndDelete({
        _id: id,
        userId: token.id,  // Ensure it's the user's chat
      });

      if (!chat) {
        return res.status(404).json({ error: 'Chat not found' });
      }

      res.status(200).json({ message: 'Chat deleted successfully' });  // Success message
    } catch (error) {
      res.status(500).json({ message: 'Error deleting chat', error: error.message });  // Internal server error
    }
  } else {
    res.setHeader('Allow', ['GET', 'PUT', 'DELETE']);
    res.status(405).end(`Method ${req.method} Not Allowed`);  // Handle invalid methods
  }
}
