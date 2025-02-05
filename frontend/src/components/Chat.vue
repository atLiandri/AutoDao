<template>
    <v-row class="h-100">
      <v-col cols="12" class="d-flex flex-column justify-end">
        <!-- <v-card class="flex-grow-1 overflow-y-auto" flat> -->
          <v-list style="padding: 0px !important;">
            <v-list-item
              v-for="(message, index) in messages"
              :key="index"
              :class="message.sender === 'user' ? 'text-right' : 'text-left'"
            >
              <v-list-item-content>
                <v-card
                  :color="message.sender === 'user' ? 'primary' : 'grey lighten-3'"
                  dark
                  class="pa-3 rounded-lg d-inline-block"
                  max-width="70%"
                >
                  <span>{{ message.text }}</span>
                </v-card>
              </v-list-item-content>
            </v-list-item>
          </v-list>
        <!-- </v-card> -->
        
        <div 
          class="pt-3 px-3 pb-2 bg-grey-darken-4 rounded elevation"
          style="border: 1px solid whitesmoke"
        >
          <div class="d-flex flex-column">
            <textarea
              v-model="newMessage" 
              style="height: 72px; margin-bottom: 8px; outline: none; resize: none;"
              @keypress.enter="sendMessage"
            ></textarea>
            <div class="d-flex justify-end">
              <button class="rounded-circle" style="padding: 4px;" @click="sendMessage">
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
    background: url('../../public/arrow-next.svg');
    background-repeat: no-repeat;
    background-position: center;
    width: 24px;
    height: 24px;
  }
  button {
    color: whitesmoke;
    border: 1px solid whitesmoke;
    display: flex;
    justify-content: center;
    align-items: center;
  }
</style>

<script>
import { ChatService } from '@/services';

export default {
  name: "Chat",
  data() {
    return {
      messages: [],
      newMessage: "",
    };
  },
  methods: {
    async sendMessage() {
      if (this.newMessage.trim() === "") return;
      let message = this.newMessage;

      this.messages.push({ text: message, sender: "user" });

      this.newMessage = "";
      const result = await ChatService.chat(message);

      this.messages.push({ text: result.parsed_content.response, sender: "bot" });
    },
  }
}
</script>