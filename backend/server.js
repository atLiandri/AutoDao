// server.js (Backend)
import express from "express";
import { MongoClient, ServerApiVersion } from "mongodb";
import cors from "cors";
import dotenv from "dotenv";
import { ethers } from "ethers";

dotenv.config();
const app = express();
app.use(express.json());
app.use(cors());

const privateKey = process.env.PRIVATE_KEY;
const uri = process.env.MONGO_URI;
const INFURA_API_KEY = process.env.API_KEY;

const provider = new ethers.providers.JsonRpcProvider(`https://base-sepolia.infura.io/v3/${INFURA_API_KEY}`);
const wallet = new ethers.Wallet(privateKey, provider);

const contractAddress = "0x9AF19d7C1d866543816a2A649E32Ab86b0Be3C39"; 
const contractABI = [
	{
		"inputs": [
			{
				"internalType": "uint16",
				"name": "_proposalId",
				"type": "uint16"
			}
		],
		"name": "voteOnProposal",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
];

const contract = new ethers.Contract(
  contractAddress, 
  contractABI, 
  wallet
);

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
});

app.post("/api/vote", async (req, res) => {
  try {
    const {proposalId } = req.body;
    const proposal = await contract.voteOnProposal(proposalId, {
      gasPrice: ethers.utils.parseUnits('10', 'gwei'),
    });
    res.status(200).json({ proposal: proposal });
  } catch(err) {
    console.log(err);
    res.status(500).json({ error: "Failed to update data" });
  }
});


// Start Server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
