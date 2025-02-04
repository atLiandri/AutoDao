<template>
  <v-main>
    <v-col cols="2">
    </v-col>
    <v-col cols="10" class="align-center">
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
  </v-main>
</template>