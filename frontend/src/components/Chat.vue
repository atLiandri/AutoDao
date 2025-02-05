<template>
    <v-row class="h-100">
      <v-col cols="12" class="d-flex flex-column">
        <v-card class="flex-grow-1 overflow-y-auto" flat>
          <v-list>
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
        </v-card>
        
        <v-card flat class="mt-4">
          <v-textarea
            v-model="newMessage"
            label="Type your message"
            outlined
            rows="2"
            auto-grow
            hide-details
            append-icon="mdi-send"
            @click:append="sendMessage"
            @keydown.enter="sendMessage"
          ></v-textarea>
        </v-card>
      </v-col>
    </v-row>
</template>

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