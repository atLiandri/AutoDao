<template>
  <v-main style="height: 100dvh">
    <v-row style="margin: auto; max-width: 80%; height: 100%; padding-top: 32px;">
      <v-col cols="5" class="h-100">
        <Chat/>
      </v-col>
      <v-col cols="7" class="h-100">
        <Proposal 
          v-for="proposal in proposals"
          actor="AI"
          :title="proposal.title"
          :subtitle="proposal.subtitle"
          :text="proposal.text"
        /> 
        <!-- <Proposal 
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
        /> -->
      </v-col>
    </v-row>
  </v-main>
</template>

<script>
import Chat from './Chat.vue';
import Proposal from './Proposal.vue';
import { ProposalService } from '@/services';

export default {
  name: 'Home',
  components: {
    Chat, 
    Proposal
  },
  data() {
    return {
      proposals: [],
    }
  },
  async created() {
    this.proposals = await ProposalService.getProposals();
  }
}
</script>