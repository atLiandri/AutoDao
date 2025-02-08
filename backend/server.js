// server.js (Backend)
import express from "express";
import { MongoClient, ServerApiVersion } from "mongodb";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();
const app = express();
app.use(express.json());
app.use(cors());

const uri = process.env.MONGO_URI;

console.log(uri);

const client = new MongoClient(uri, {
  serverApi: {
    version: ServerApiVersion.v1,
    strict: true,
    deprecationErrors: true,
  }
});

async function connectDB() {
  try {
    await client.connect();
    console.log("Connected to MongoDB!");
  } catch (err) {
    console.error("Error connecting to MongoDB:", err);
  }
}

connectDB();

app.get("/api/proposals", async (req, res) => {
  try {
    const db = client.db("proposals");
    const collection = db.collection("proposals");
    const data = await collection.find().toArray();
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: "Failed to fetch data" });
  }
});

app.post("/api/proposals", async (req, res) => {
  try {
    const db = client.db("proposals");
    const collection = db.collection("proposals");
    collection.insertOne(req.body);
    res.status(200).json({ message: "Ok"});
  } catch (err) {
    res.status(500).json({ error: "Failed to update data" });
  }
})

// Start Server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
