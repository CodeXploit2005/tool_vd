CREATE TYPE "public"."aspect_ratio" AS ENUM('9:16', '16:9');--> statement-breakpoint
CREATE TYPE "public"."niche_format" AS ENUM('story', 'ambient', 'wordless');--> statement-breakpoint
CREATE TYPE "public"."posts_status" AS ENUM('none', 'writing', 'ready', 'failed');--> statement-breakpoint
CREATE TYPE "public"."project_status" AS ENUM('scripting', 'script_ready', 'producing', 'rendering', 'done', 'failed');--> statement-breakpoint
CREATE TYPE "public"."reference_status" AS ENUM('none', 'generating', 'ready', 'failed');--> statement-breakpoint
CREATE TYPE "public"."scene_status" AS ENUM('pending', 'keyframe', 'video', 'done', 'failed');--> statement-breakpoint
CREATE TYPE "public"."short_status" AS ENUM('rendering', 'ready', 'failed');--> statement-breakpoint
CREATE TYPE "public"."thumbnail_status" AS ENUM('none', 'drawing', 'ready', 'failed');--> statement-breakpoint
CREATE TABLE "characters" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"name" text NOT NULL,
	"appearance" text NOT NULL,
	"personality" text DEFAULT '' NOT NULL,
	"reference_image_path" text,
	"reference_status" "reference_status" DEFAULT 'none' NOT NULL,
	"reference_error" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "facebook_pages" (
	"id" text PRIMARY KEY NOT NULL,
	"name" text NOT NULL,
	"access_token" text NOT NULL,
	"instagram_id" text,
	"instagram_username" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "niche_characters" (
	"niche_id" uuid NOT NULL,
	"character_id" uuid NOT NULL,
	"position" integer NOT NULL,
	CONSTRAINT "niche_characters_niche_id_character_id_pk" PRIMARY KEY("niche_id","character_id")
);
--> statement-breakpoint
CREATE TABLE "niches" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"slug" text NOT NULL,
	"name" text NOT NULL,
	"description" text DEFAULT '' NOT NULL,
	"script_instructions" text NOT NULL,
	"tone" text DEFAULT '' NOT NULL,
	"visual_style" text DEFAULT '' NOT NULL,
	"scene_count" integer DEFAULT 6 NOT NULL,
	"scene_seconds" integer DEFAULT 10 NOT NULL,
	"language" text DEFAULT 'Vietnamese' NOT NULL,
	"icon" text DEFAULT '✦' NOT NULL,
	"format" "niche_format" DEFAULT 'story' NOT NULL,
	"fixed_camera" boolean DEFAULT false NOT NULL,
	"default_aspect_ratio" "aspect_ratio" DEFAULT '9:16' NOT NULL,
	"narrator_voice_id" text,
	"thumbnail_style" text DEFAULT 'impact' NOT NULL,
	"thumbnail_accent" text DEFAULT '#FFC23D' NOT NULL,
	"thumbnail_brand" text DEFAULT '' NOT NULL,
	"posts_instructions" text DEFAULT '' NOT NULL,
	"facebook_page_id" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "niches_slug_unique" UNIQUE("slug")
);
--> statement-breakpoint
CREATE TABLE "project_characters" (
	"project_id" uuid NOT NULL,
	"character_id" uuid NOT NULL,
	"position" integer NOT NULL,
	CONSTRAINT "project_characters_project_id_character_id_pk" PRIMARY KEY("project_id","character_id")
);
--> statement-breakpoint
CREATE TABLE "projects" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"title" text NOT NULL,
	"topic" text NOT NULL,
	"niche_id" uuid NOT NULL,
	"aspect_ratio" "aspect_ratio" NOT NULL,
	"status" "project_status" DEFAULT 'scripting' NOT NULL,
	"error" text,
	"final_video_path" text,
	"captions_path" text,
	"audio_path" text,
	"audio_seconds" real,
	"scene_count" integer,
	"script_source" text DEFAULT 'generated' NOT NULL,
	"reference_image_path" text,
	"reference_image_kind" text DEFAULT 'place' NOT NULL,
	"product_image_paths" jsonb DEFAULT '[]'::jsonb NOT NULL,
	"posts" jsonb,
	"posts_status" "posts_status" DEFAULT 'none' NOT NULL,
	"posts_error" text,
	"thumbnail" jsonb,
	"thumbnail_status" "thumbnail_status" DEFAULT 'none' NOT NULL,
	"thumbnail_error" text,
	"shorts_status" "posts_status" DEFAULT 'none' NOT NULL,
	"shorts_error" text,
	"facebook_reel" jsonb,
	"instagram_reel" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "scenes" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"project_id" uuid NOT NULL,
	"index" integer NOT NULL,
	"narration" text NOT NULL,
	"visual_prompt" text NOT NULL,
	"camera" text DEFAULT '' NOT NULL,
	"status" "scene_status" DEFAULT 'pending' NOT NULL,
	"keyframe_path" text,
	"clip_path" text,
	"continues_previous" boolean DEFAULT false NOT NULL,
	"character_ids" uuid[] DEFAULT '{}'::uuid[] NOT NULL,
	"error" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "shorts" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"project_id" uuid NOT NULL,
	"index" integer NOT NULL,
	"from_scene" integer NOT NULL,
	"to_scene" integer NOT NULL,
	"hook" text NOT NULL,
	"title" text NOT NULL,
	"description" text DEFAULT '' NOT NULL,
	"status" "short_status" DEFAULT 'rendering' NOT NULL,
	"video_path" text,
	"error" text,
	"facebook_reel" jsonb,
	"instagram_reel" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "niche_characters" ADD CONSTRAINT "niche_characters_niche_id_niches_id_fk" FOREIGN KEY ("niche_id") REFERENCES "public"."niches"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "niche_characters" ADD CONSTRAINT "niche_characters_character_id_characters_id_fk" FOREIGN KEY ("character_id") REFERENCES "public"."characters"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "project_characters" ADD CONSTRAINT "project_characters_project_id_projects_id_fk" FOREIGN KEY ("project_id") REFERENCES "public"."projects"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "project_characters" ADD CONSTRAINT "project_characters_character_id_characters_id_fk" FOREIGN KEY ("character_id") REFERENCES "public"."characters"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "projects" ADD CONSTRAINT "projects_niche_id_niches_id_fk" FOREIGN KEY ("niche_id") REFERENCES "public"."niches"("id") ON DELETE restrict ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "scenes" ADD CONSTRAINT "scenes_project_id_projects_id_fk" FOREIGN KEY ("project_id") REFERENCES "public"."projects"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "shorts" ADD CONSTRAINT "shorts_project_id_projects_id_fk" FOREIGN KEY ("project_id") REFERENCES "public"."projects"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE UNIQUE INDEX "scenes_project_index_uq" ON "scenes" USING btree ("project_id","index");--> statement-breakpoint
CREATE UNIQUE INDEX "shorts_project_index_uq" ON "shorts" USING btree ("project_id","index");