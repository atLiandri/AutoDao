<template>
  <v-card
    class="mx-auto my-8"
    elevation="16"
    max-width="344"
    :prepend-icon="getIcon"
  >
    <v-card-item>
      <v-card-title>
        {{ title }}
      </v-card-title>

      <v-card-subtitle>
        {{ subtitle }}
      </v-card-subtitle>
    </v-card-item>

    <v-card-text>
      {{ text }}
    </v-card-text>
    <v-card-actions class="align-right justify-end">
      <v-btn @click="voteOnProposal" :disabled="disabled">
        Accept
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import detectEthereumProvider from "@metamask/detect-provider"
import { ethers } from 'ethers';

export default {
  name: "Proposal",
  props: {
    actor: {
      type: String,
      default: ""
    },
    title: {
      type: String,
      default: ""
    },
    subtitle: {
      type: String,
      default: "",
    },
    text: {
      type: String,
      default: ""
    }
  },
  data: () => ({
    disabled: false
  }),
  computed: {
    getIcon() {
      switch(this.actor) {
        case "AI":
          return "mdi-robot";
        case "Gov":
          return "mdi-gavel";
        default:
          return "mdi-account";  
      }
    }
  },
  methods: {
    async voteOnProposal() {
      const provider = await detectEthereumProvider();
      if (provider && provider === window.ethereum) {
        const ethersProvider = new ethers.BrowserProvider(provider);
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
        const signer = await ethersProvider.getSigner();
        const contract = new ethers.Contract(
          contractAddress, 
          contractABI, 
          signer
        );
        await contract.voteOnProposal(1, {
          gasPrice: ethers.parseUnits('10', 'gwei'),
        });
        this.disabled = true;
      } else {
        console.log("Please install MetaMask!")
      }
    }
  }
}
</script>