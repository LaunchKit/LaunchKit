/**
 * @license
 * Copyright 2016 Cluster Labs, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

var Select = React.createClass({
  render: function() {
    if (this.props.valueLink) {
      return (
        <select className="form-control form-control-select" name={this.props.name} valueLink={this.props.valueLink}>
          {this.props.options.map(function(k, i){
            var label = (this.props.labelKey) ? k[this.props.labelKey] : k.label;
            var value = (this.props.valueKey) ? k[this.props.valueKey] : k.value;
            return <option key={i} value={value}>{label}</option>
          }, this)}
        </select>
      )
    } else {
      return (
        <select className="form-control form-control-select" name={this.props.name} onChange={this.props.onChange} value={this.props.selected}>
          {this.props.options.map(function(k, i){
            var label = (this.props.labelKey) ? k[this.props.labelKey] : k.label;
            var value = (this.props.valueKey) ? k[this.props.valueKey] : k.value;
            return <option key={i} value={value}>{label}</option>
          }, this)}
        </select>
      )
    }
  }
})

module.exports = Select;