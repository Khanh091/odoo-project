/** @odoo-module **/

import {
    Many2ManyBinaryField,
    many2ManyBinaryField,
} from "@web/views/fields/many2many_binary/many2many_binary_field";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class TctMany2ManyBinaryField extends Many2ManyBinaryField {
    static template = "tct_file_preview.AttachmentPreviewGallery";

    setup() {
        super.setup();
        this.action = useService("action");
    }

    getPreviewUrl(file) {
        if (file.mimetype && file.mimetype.startsWith("image/")) {
            return `/web/image/ir.attachment/${file.id}/datas`;
        }
        return false;
    }

    formatFileSize(size) {
        if (!size) {
            return "";
        }
        if (size < 1024) {
            return `${size} B`;
        }
        if (size < 1024 * 1024) {
            return `${(size / 1024).toFixed(1)} KB`;
        }
        return `${(size / (1024 * 1024)).toFixed(1)} MB`;
    }

    async onPreview(fileId) {
        const action = await this.orm.call(
            "ir.attachment",
            "action_preview_file",
            [[fileId]]
        );
        if (!action.views) {
            action.views = [[false, "form"]];
        }
        await this.action.doAction(action);
    }
}

export const tctMany2ManyBinaryField = {
    ...many2ManyBinaryField,
    component: TctMany2ManyBinaryField,
    relatedFields: [
        ...many2ManyBinaryField.relatedFields,
        { name: "file_size", type: "integer" },
        { name: "can_preview", type: "boolean" },
    ],
};

registry.category("fields").add(
    "many2many_binary",
    tctMany2ManyBinaryField,
    { force: true }
);
