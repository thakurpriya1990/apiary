<template lang="html">
    <div>
        <div class="form-group"><div class="row">
            <label class="col-sm-2">Period From</label>
            <div class="col-sm-4">
                <div class="input-group date" ref="periodFromDatePicker">
                    <input type="date" class="form-control" placeholder="DD/MM/YYYY" id="period_from_input_element" v-model="period_from" :disabled="is_readonly"/>
                </div>
            </div>
        </div></div>

        <div class="form-group"><div class="row">
            <label class="col-sm-2">Period To</label>
            <div class="col-sm-4">
                <div class="input-group date" ref="periodToDatePicker">
                    <input type="date" class="form-control" placeholder="DD/MM/YYYY" id="period_to_input_element" v-model="period_to" :disabled="is_readonly"/>
                </div>
            </div>
        </div></div>

        <ComponentSiteSelection
            :apiary_sites="apiary_sites"
            :is_internal="false"
            :is_external="true"
            :enable_col_checkbox="is_checkbox_enabled"
            :key="component_site_selection_key"
            @apiary_sites_updated="apiarySitesUpdated"
        />

    </div>
</template>

<script>
    import ComponentSiteSelection from '@/components/common/apiary/component_site_selection.vue'
    import { v4 as uuid } from 'uuid';

    export default {
        name: 'SectionPeriodAndSites',
        props:{
            // If editing an existing proposal apiary temporary use, data is passed from the parent component
            from_date: {
                type: Object,
                default: null,
            },
            // If editing an existing proposal apiary temporary use, data is passed from the parent component
            to_date: {
                type: Object,
                default: null,
            },
            // array of intermediate table, TemporaryUseApiarySite
            temporary_use_apiary_sites: {
                type: Array,
                default: function(){
                    return [];
                }
            },
            // all the ProposalApiaryTemporaryUse use objects under this licence
            // to be used to calculate each apirary site availability at any moment given
            existing_temporary_uses: {
                type: Array,
                default: function(){
                    return [];
                }
            },
            is_external:{
              type: Boolean,
              default: false
            },
            is_internal:{
              type: Boolean,
              default: false
            },
            is_readonly: {
              type: Boolean,
              default: true
            },
            customer_status: {
                type: String,
                default: ''
            },
            processing_status: {
                type: String,
                default: ''
            }
        },
        data:function () {
            return{
                component_site_selection_key: '',
                period_from: '',
                period_to: '',
                //period_from_enabled: false,
                //period_to_enabled: false,
                apiary_sites: [],  // Used to construct the sites table
                                                 // Array of TemporaryUseApiarySite objects
            }
        },
        created: function() {
            // Copy the values from props (it is not allowd to change props' value)
            console.log(this.from_date)
            if (this.from_date){
                this.period_from = this.from_date.format('YYYY-MM-DD');
                console.log(this.period_from)
            }
            if (this.to_date){
                this.period_to = this.to_date.format('YYYY-MM-DD');
            }
            if (this.temporary_use_apiary_sites.length > 0){
                for (let i=0; i<this.temporary_use_apiary_sites.length; i++){
                    let site = this.temporary_use_apiary_sites[i].apiary_site

                    // Add the status of the checkbox for this apiary site if needed
                    // otherwise the default status is unchecked
                    site.checked = this.temporary_use_apiary_sites[i].selected

                    this.apiary_sites.push(site)
                }
            }
            this.component_site_selection_key = uuid()
        },
        components: {
            ComponentSiteSelection,
        },
        computed:{
            is_checkbox_enabled: function() {
                let enabled = false
                if(this.is_external){
                    if(['Draft', 'draft'].includes(this.customer_status)){
                        enabled = true
                    }
                }
                return enabled
            }
        },
        methods:{
            apiarySitesUpdated: function(apiary_sites){
                console.log(apiary_sites[0])
                this.$emit('apiary_sites_updated', apiary_sites)
            },
        },
        watch: {
            period_from: function() {
                this.$nextTick(() => {
                    this.$emit('from_date_changed',this.period_from)
                });
            },
            period_to: function() {
                this.$nextTick(() => {
                    this.$emit('to_date_changed',this.period_to)
                });
            }
        }
    }
</script>

<style lang="css" scoped>

</style>
