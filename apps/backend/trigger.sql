CREATE OR REPLACE FUNCTION sync_feature_attributes()
RETURNS TRIGGER AS $$
DECLARE
    style_json jsonb;
    attributes_json jsonb;
BEGIN
    -- Initialize _attributes as an empty JSON object if it's NULL
    IF NEW._attributes IS NULL THEN
        NEW._attributes := '{}'::jsonb;
    END IF;

    -- Build the style JSON object from style fields
    style_json := jsonb_build_object();
    IF NEW.style_color IS NOT NULL AND NEW.style_color <> '' THEN
        style_json := style_json || jsonb_build_object('color', NEW.style_color);
    END IF;
    IF NEW.style_opacity IS NOT NULL THEN
        style_json := style_json || jsonb_build_object('opacity', NEW.style_opacity);
    END IF;
    IF NEW.style_weight IS NOT NULL THEN
        style_json := style_json || jsonb_build_object('weight', NEW.style_weight);
    END IF;

    -- Build the main attributes JSON object
    attributes_json := jsonb_build_object();
    IF NEW.name IS NOT NULL AND NEW.name <> '' THEN
        attributes_json := attributes_json || jsonb_build_object('name', NEW.name);
    END IF;
    IF NEW.description IS NOT NULL AND NEW.description <> '' THEN
        attributes_json := attributes_json || jsonb_build_object('description', NEW.description);
    END IF;
    IF jsonb_build_object() <> style_json THEN
        attributes_json := attributes_json || jsonb_build_object('style', style_json);
    END IF;

    -- Merge the generated attributes with existing ones, generated ones take precedence
    NEW._attributes := NEW._attributes || attributes_json;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop the trigger if it already exists to avoid errors on re-run
DROP TRIGGER IF EXISTS features_sync_trigger ON features;

-- Create the trigger
CREATE TRIGGER features_sync_trigger
BEFORE INSERT OR UPDATE ON features
FOR EACH ROW EXECUTE FUNCTION sync_feature_attributes();
