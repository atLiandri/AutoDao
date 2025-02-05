<template>
  <v-app>
    <v-app-bar>
    </v-app-bar>
    <RouterView></RouterView>
  </v-app>
</template>

<script>
import Proposal from './components/Proposal.vue';

export default {
  name: "App",
  components: {
    Proposal,
  }
}
</script>
