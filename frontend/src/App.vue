<template>
  <v-app>
    <v-app-bar>
    </v-app-bar>
    <RouterView></RouterView>
  </v-app>
</template>

<style>
@import "../public/styles.css";
</style>

<script>
import Proposal from './components/Proposal.vue';

export default {
  name: "App",
  components: {
    Proposal,
  }
}
</script>
