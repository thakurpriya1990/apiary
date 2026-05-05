<template lang="html">
    <div class="card card" >
      <div v-if="!hideHeader" class="card-header">
        <h3 class="card-title">{{label}} <small v-if="subheading"> - {{subheading}}</small> 
            <a :href="'#'+section_id" class="panelClicker" :id="custom_id" data-bs-toggle="collapse" expanded="true" :aria-controls="section_id">
                <span :class="panel_chevron_class"></span>
            </a>
        </h3>
      </div>
      <div :class="panel_collapse_class" :id="section_id">
          <slot></slot>
      </div>
    </div>
</template>

<script>
import { v4 as uuid } from 'uuid';
import $ from 'jquery';

export default {
    name:"FormSection",
    props:{
        "label": {
            type: String,
            default: ''
        },
        "subheading":{
            type: String,
            default: ''
        },
        "Index":{
            type: String,
            default: ''
        },
        "formCollapse":{
            type: Boolean,
            default: false
        },
        "hideHeader": {
            type: Boolean,
            default: false
        },
        "treeHeight": {
            type: Boolean,
            default: false
        },
    },
    data:function () {
        return {
            title:"Section title",
            panel_chevron_class: null,
            custom_id: uuid(),
        }
    },
    computed:{
        section_id: function () {
            return "section_"+this.Index
        },
        panel_collapse_class: function() {
            if (this.formCollapse) {
                // this.panel_chevron_class = "fa fa-chevron-down float-end";
                return "card-body collapse";
            } else {
                if (this.treeHeight) {
                    // this.panel_chevron_class = "fa fa-chevron-up float-end";
                    return "card-body collapse show flex-container";
                } else {
                    // this.panel_chevron_class = "fa fa-chevron-up float-end";
                    return "card-body collapse show";
                }
            }
        },
    },
    mounted: function() {
        $('#' + this.custom_id).on('click',function () {
            var chev = $(this).children()[0];
            window.setTimeout(function () {
                $(chev).toggleClass("fa-chevron-up fa-chevron-down");
            }, 100);
        });
    },
    updated:function () {
    },
}
</script>

<style lang="css">
    h3.card-title{
        font-weight: bold;
        font-size: 25px;
        padding:20px;
    }
    .flex-container {
        display: flex;
        flex-direction: column;
        min-height: 325px;
    }
</style>
