<template>
  <v-app>
    <v-app-bar>
    <v-container class="d-flex justify-center">
      <v-btn to="/"> Home </v-btn>
      <v-btn to="/chat"> Chat </v-btn>
      <v-btn to="/profile"> Your profile </v-btn>
    </v-container>
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
