<template>
  <v-main style="height: 100dvh">
    <v-row style="margin: auto; max-width: 80%; height: 100%; padding-top: 32px;">
      <v-col cols="5" class="h-100">
        <Chat
          @proposal="addNewProposal"
        />
      </v-col>
      <v-col cols="7" class="h-100">
        <Proposal 
          v-for="proposal in this.proposals"
          actor="AI"
          :title="proposal.parsed_content.title"
          :subtitle="proposal.parsed_content.summary"
          :text="proposal.parsed_content.response"
        /> 
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
  data: () => ({
    proposals: [],
  }),
  async created() {
    const data = await ProposalService.getProposals();
    this.proposals.splice(0, this.proposals.length, ...data);
  },
  methods: {
    addNewProposal(proposal) {
      this.proposals.push(proposal);
    }
  }
}
</script>