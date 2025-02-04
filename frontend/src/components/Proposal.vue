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
      <v-btn>
        Accept
      </v-btn>
      <v-btn>
        Reject
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
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
  }
}
</script>