<template>
<div id="app">
  <router-view></router-view>
</div>
</template>

<script>
export default {
  name: 'app'
}


</script>

<style>
.popover {
    max-width: 100% !important;
}
.select2-container--disabled, .select2-container--focus{
    z-index: 1;
}
/* Fix select2 4.1.x choice remove button rendered as <button> conflicting with Bootstrap 3 button styles */
.select2-selection__choice__remove {
    background: none;
    border: none;
    padding: 0;
    margin: 0;
    line-height: 1;
    box-shadow: none;
    font-size: inherit;
}
</style>
