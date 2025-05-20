<template>
    <div>
        <template v-if="assessorMode">
        <template v-if="!showingComment">
            <!-- <a v-if="comment_value != null && comment_value != undefined && comment_value != ''" href="" @click.prevent="toggleComment"><i style="color:red" class="fa fa-comment-o">&nbsp;</i></a> -->
            <a v-if="has_comment_value" href="" @click.prevent="toggleComment"><i style="color:red" class="fa fa-comment-o">&nbsp;</i></a>
            <a v-else href="" @click.prevent="toggleComment"><i class="fa fa-comment-o">&nbsp;</i></a>
        </template>
        <a href="" v-else  @click.prevent="toggleComment"><i class="fa fa-ban">&nbsp;</i></a>
        </template>
        <!-- <Comment :question="label" :readonly="assessor_readonly" :name="name+'-comment-field'" v-show="showingComment && assessorMode" :value="comment_value"/>  -->
        <CommentBox :comment_boxes="JSON.parse(comment_boxes)" v-show="showingComment && assessorMode"/> 
    </div>
</template>
<script>
import Comment from './comment.vue'
import CommentBox from './comment_box_referral.vue'
export default {
    name:"Checkbox-comment-icon",
    props:["name","comment_value","assessorMode","label","assessor_readonly","comment_boxes",],
    components: {Comment, CommentBox},
    data(){
        let vm = this;
        return {
            showingComment: false
        }
    },
    computed:{
        has_comment_value:function () {
            let has_value=false;
            for(var i=0; i<this.comment_boxes.length; i++){
                if(this.comment_boxes[i].hasOwnProperty('value')){
                    if(this.comment_boxes[i].value!=null && this.comment_boxes[i].value!=undefined && this.comment_boxes[i].value!= '' ){
                        has_value=true;
                    }
                } 
            }
            return has_value;
        },
    },
    methods: {
        toggleComment(){
            this.showingComment = ! this.showingComment;
        }
    }
}
</script>
