from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Load noupdate changes
    openupgrade.load_data(env.cr, "website_slides", "15.0.2.4/noupdate_changes.xml")
    openupgrade.delete_record_translations(
        env.cr,
        "website_slides",
        [
            "mail_template_slide_channel_invite",
            "slide_template_published",
            "slide_template_shared",
            "mail_notification_channel_invite",
        ],
    )
    update_color_for_slide_channel_tag(env)
    update_translation_type_for_description_fields(env)


def update_translation_type_for_description_fields(env):
    # Update the translation type for the fields: description, description_short of
    # (slide.slide and slide.channel) because they are converted from text to html
    # Type model -> model_terms
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_translation
        SET type = 'model_terms'
        WHERE
            type ='model'
            AND name IN (
                'slide.channel,description',
                'slide.channel,description_short',
                'slide.slide,description'
            )
        """,
    )


def update_color_for_slide_channel_tag(env):
    # We need to update the color of the tag because the course page only shows tags with colors
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE slide_channel_tag
        SET color = floor(random() * 11 + 1)
        WHERE color IS NULL OR color = 0
        """,
    )
