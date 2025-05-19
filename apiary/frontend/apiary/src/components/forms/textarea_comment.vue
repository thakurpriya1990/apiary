<template lang="html">
    <div >
           <textarea :readonly="readonly" :type="type" :class="box_class" :name="name" :value="value" :data-question="question"></textarea>
              
              <!-- <label :id="id" class="col-md-3" for="label" >{{ label }}</label> -->
              <!-- <div class="col-md-9" v-if="box.referral_box">
                  <textarea :readonly="box.readonly" :type="box.type" :class="box.box_class" :name="box.name" :value="box.value" :data-question="box.question"></textarea>
              </div>
              <div class="col-md-9" v-else>
                  <textarea :readonly="box.readonly" :type="box.type" :class="box.box_class" :name="box.name" :value="box.value" :data-question="box.question"></textarea>
              </div> -->         
    </div>
</template>

<script>
export default {
    props:["value", "id", "type", "name", "question","readonly", "label", "box_class"]
}
</script>

<style lang="css">
</style>