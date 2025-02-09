<template>
  <v-row class="h-100">
    <v-col cols="12" class="d-flex flex-column justify-end h-100">
      <v-list
        style="
          padding: 0px !important;
          background-color: transparent !important;
          overflow-y: auto;
          scroll-behavior: smooth;
        "
        class="mb-4"
      >
        <v-list-item
          v-for="(message, index) in messages"
          :key="index"
          :class="message.sender === 'user' ? 'text-right' : 'text-left'"
        >
          <v-list-item-content>
            <v-card
              :color="message.sender === 'user' ? '#eeeeee' : 'grey lighten-3'"
              class="pa-3 rounded-lg d-inline-block"
              max-width="70%"
            >
              <span>{{ message.text }}</span>
            </v-card>
          </v-list-item-content>
        </v-list-item>
      </v-list>

      <div
        class="pt-3 px-3 pb-2 bg-grey-darken-4 rounded elevation"
        style="border: 1px solid #373a40"
      >
        <div class="d-flex flex-column">
          <textarea
            v-model="newMessage"
            style="
              height: 72px;
              margin-bottom: 8px;
              outline: none;
              resize: none;
            "
            @keypress.enter="sendMessage"
          ></textarea>
          <div class="d-flex justify-end">
            <button
              class="rounded-circle"
              style="padding: 4px"
              @click="sendMessage"
            >
              <i class="chevron-right"></i>
            </button>
          </div>
        </div>
      </div>
    </v-col>
  </v-row>
</template>

<style scoped>
.chevron-right {
  background: url("../../public/arrow-next.svg");
  background-repeat: no-repeat;
  background-position: center;
  width: 24px;
  height: 24px;
}

button:hover {
  border-color: #eeeeee;
}

button:active {
  transform: scale(0.9);
}

button:hover .chevron-right {
  background: url("../../public/arrow-next-hover.svg");
  background-repeat: no-repeat;
  background-position: center;
  width: 24px;
  height: 24px;
}

button {
  border: 1px solid #5a5f69;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.2s ease-in-out;
}
</style>

<script>
import { ChatService, ProposalService } from "@/services";

export default {
  name: "Chat",
  data() {
    return {
      messages: [],
      newMessage: "",
    };
  },
  emits: ['proposal'],
  methods: {
    async sendMessage() {
      if (this.newMessage.trim() === "") return;
      let message = this.newMessage;

      this.messages.push({ text: message, sender: "user" });

      this.newMessage = "";
      const result = await ChatService.chat(message);

      if (result.transaction_hash) {
        ProposalService.postProposal(result);

        this.messages.push({
          text: "I have created a proposal for you, mate. Cheers!",
          sender: "bot",
        });
        this.$emit("proposal", result);
      } else {
        this.messages.push({
          text: result.parsed_content.response,
          sender: "bot",
        });
      }
    },
  },
};
</script>