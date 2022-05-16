// Copyright 2021-2022  Kevin Murray, MPI Biologie Tübingen
// Copyright 2021-2022  Gekkonid Consulting
//
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

import Vue from 'vue/dist/vue.js';
import LabelTypes from './labeltypes.json';

require("milligram/dist/milligram.min.css");

var vm = new Vue({
    el: "#labsheet",
    data: {
        labelType: false,
        layout: false,
        labelTypes: LabelTypes,
        cells: [],
        nrow: 0,
        ncol: 0
    },
    computed: {
        command() {
            const lt = this.$data.labelTypes[this.$data.labelType].name;
            const layout = this.$data.layout;
            return `qrmagic-labelprint --output labels.pdf --id-file labels.txt --label-type ${lt} --layout ${layout}`;
        }
    },
    methods: {
        async labelTypeUpdate(e) {
            const lt = this.$data.labelTypes[this.$data.labelType];
            this.$data.layout = lt.default_layout;
            this.$data.nrow = lt.nrow;
            this.$data.ncol = lt.ncol;
            const len = lt.nrow * lt.ncol;
            while (this.$data.cells.length > len) {this.$data.cells.pop();}
            while (this.$data.cells.length < len) {this.$data.cells.push("");}

        },
        async downloadLabelTxtFile() {
            console.log(this.$data);
            // Download file
            var element = document.createElement('a');
            element.style.display = 'none';
            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(this.$data.cells.join("\n")));
            element.setAttribute('download', "labels.txt");
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
            console.log(this.$data.cells);
        }
    }
});
