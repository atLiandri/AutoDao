<template>
  <v-main>
    <v-row class="h-100" style="margin: auto; max-width: 80%;">
      <v-col cols="5">
        <Chat/>
      </v-col>
      <v-col cols="7">
        <Proposal 
          actor="AI"
          title="My suggestion"
          subtitle="Kill all humans!"
          text="A lot of killing here and there!"
        />
        <Proposal 
          actor="User"
          title="Wall Painting"
          subtitle="Reeeed"
          text="Can we paint the walls red?"
        />
        <Proposal 
          actor="Gov"
          title="Taxes"
          subtitle="We increase the taxes"
          text="We would like you to pay more taxes!"
        />
      </v-col>
    </v-row>
  </v-main>
</template>

<script>
import Chat from './Chat.vue';
import Proposal from './Proposal.vue';

export default {
  name: 'Home',
  components: {
    Chat, 
    Proposal
  }
}
</script>
