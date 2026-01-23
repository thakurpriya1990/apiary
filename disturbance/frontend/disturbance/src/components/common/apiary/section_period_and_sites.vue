<template lang="html">
    <div>
        <div class="form-group"><div class="row">
            <label class="col-sm-2">Period From</label>
            <div class="col-sm-4">
                <div class="input-group date" ref="periodFromDatePicker">
                    <input type="date" class="form-control" placeholder="DD/MM/YYYY" id="period_from_input_element" :v-model="from_date" :disabled="is_readonly"/>
                </div>
            </div>
        </div></div>

        <div class="form-group"><div class="row">
            <label class="col-sm-2">Period To</label>
            <div class="col-sm-4">
                <div class="input-group date" ref="periodToDatePicker">
                    <input type="date" class="form-control" placeholder="DD/MM/YYYY" id="period_to_input_element" :v-model="to_date" :disabled="is_readonly"/>
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
                type: Object, // Expect moment obj
                default: null,
            },
            // If editing an existing proposal apiary temporary use, data is passed from the parent component
            to_date: {
                type: Object, // Expect moment obj
                default: null,
            },
            // array of intermediate table, TemporaryUseApiarySite TODO fix for segregatin replace this for api call
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
            if (this.from_date){
                if (this.from_date instanceof moment) {
                    this.period_from = this.from_date.format('DD/MM/YYYY');
                } else {
                    // Wrong type of object, clear it
                    console.warn('The value passed to from_date is wrong type');
                    this.period_from = null;
                }
            }
            if (this.to_date){
                if (this.to_date instanceof moment) {
                    this.period_to = this.to_date.format('DD/MM/YYYY');
                } else {
                    // Wrong type of object, clear it
                    console.warn('The value passed to to_date is wrong type');
                    this.period_to = null;
                }
            }
            //TODO fix for segregation - rework temporary_use_apiary_sites - do not load from proposal load separetly
            //ideally with as few details as necessary
            //and if possible, not necessarily all at once
            //and post-draft, only load selected
            if (this.temporary_use_apiary_sites.length > 0){
                for (let i=0; i<this.temporary_use_apiary_sites.length; i++){
                    //let site = this.temporary_use_apiary_sites[i].apiary_site
                    let site = this.temporary_use_apiary_sites[i].apiary_site

                    // Add the status of the checkbox for this apiary site if needed
                    // otherwise the default status is unchecked
                    site.checked = this.temporary_use_apiary_sites[i].selected

                    this.apiary_sites.push(site)
                }
            }
            //this.period_from_enabled = this.from_date_enabled;
            //this.period_to_enabled = this.to_date_enabled;
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
                console.log(apiary_sites)
                this.$emit('apiary_sites_updated', apiary_sites)
            },
            //viewSiteOnMap: function(e){
            //    let apiary_site_id = e.target.getAttribute("data-apiary-site-id");
            //    console.log('view site-id: ' + apiary_site_id + ' on the map');
            //},
            //siteCheckboxClicked: function(e){
            //    let apiary_site_id = e.target.getAttribute("data-apiary-site-id");
            //    this.$emit('site_checkbox_clicked', {
            //        'apiary_site_id': apiary_site_id,
            //        'checked': e.target.checked
            //    });
            //},
            //constructApiarySitesTable: function(){
            //    // Clear table
            //    this.$refs.apiary_sites_table.vmDataTable.clear().draw();

            //    // Construct table
            //    if (this.apiary_sites.length > 0){
            //        for(let i=0; i<this.apiary_sites.length; i++){
            //            this.addApiarySiteToTable(this.apiary_sites[i]);
            //        }
            //    }
            //},
            //addApiarySiteToTable: function(temporary_use_apiary_site) {
            //    console.log('in addApiarySiteToTable');
            //    //apiary_site['_site_used'] = false  // Make the site be temporary usable
            //    //apiary_site['_from_and_to_date_set'] = false

            //    if (this.period_from && this.period_to){
            //        // Only when from and to dates are set
            //        //apiary_site['_from_and_to_date_set'] = true

            //    //    outer_loop:
            //    //    for (let i=0; i<this.existing_temporary_uses.length; i++){
            //    //        // Check the usability to each existing temporary_use object
            //    //        let temp_use = this.existing_temporary_uses[i];

            //    //        for (let j=0; j<temp_use.apiary_sites.length; j++){
            //    //            let item_in_inter_table = temp_use.apiary_sites[j];

            //    //            if (item_in_inter_table.apiary_site.id == apiary_site.id){
            //    //                // Check the availability of the site
            //    //                let used_from_date = moment(temp_use.from_date, 'YYYY-MM-DD');
            //    //                let used_to_date = moment(temp_use.to_date, 'YYYY-MM-DD');
            //    //                let period_from = moment(this.period_from, 'DD/MM/YYYY');
            //    //                let period_to = moment(this.period_to, 'DD/MM/YYYY');

            //    //                console.log('used_from_date');
            //    //                console.log(used_from_date);
            //    //                console.log('used_to_date');
            //    //                console.log(used_to_date);
            //    //                console.log('period_from');
            //    //                console.log(period_from);
            //    //                console.log('period_to');
            //    //                console.log(period_to);

            //    //                if (period_to < used_from_date || used_to_date < period_from){
            //    //                    // Site is not used.  Do nothing
            //    //                } else {
            //    //                    // This site is temporary used for the period from this.form_date to this.to_date
            //    //                    apiary_site['_site_used'] = true
            //    //                    break outer_loop;
            //    //                }
            //    //            }
            //    //        }
            //    //    }

            //    }

            //    this.$refs.apiary_sites_table.vmDataTable.row.add(temporary_use_apiary_site).draw();
            //},
        },
    }
</script>

<style lang="css" scoped>

</style>
