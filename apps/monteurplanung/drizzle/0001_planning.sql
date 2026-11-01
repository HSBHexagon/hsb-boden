CREATE TABLE `planning_absences` (
	`environment` text NOT NULL,
	`id` text NOT NULL,
	`worker_id` text NOT NULL,
	`payload` text NOT NULL,
	PRIMARY KEY(`environment`, `id`),
	FOREIGN KEY (`environment`,`worker_id`) REFERENCES `planning_workers`(`environment`,`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `planning_assignments` (
	`environment` text NOT NULL,
	`id` text NOT NULL,
	`worker_id` text NOT NULL,
	`project_id` text NOT NULL,
	`date` text NOT NULL,
	`payload` text NOT NULL,
	PRIMARY KEY(`environment`, `id`),
	FOREIGN KEY (`environment`,`worker_id`) REFERENCES `planning_workers`(`environment`,`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`environment`,`project_id`) REFERENCES `planning_projects`(`environment`,`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `planning_worker_day` ON `planning_assignments` (`environment`,`worker_id`,`date`);--> statement-breakpoint
CREATE TABLE `planning_meta` (
	`environment` text PRIMARY KEY NOT NULL,
	`revision` integer NOT NULL,
	`write_token` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `planning_projects` (
	`environment` text NOT NULL,
	`id` text NOT NULL,
	`number` text NOT NULL,
	`payload` text NOT NULL,
	PRIMARY KEY(`environment`, `id`)
);
--> statement-breakpoint
CREATE UNIQUE INDEX `planning_project_number` ON `planning_projects` (`environment`,`number`);--> statement-breakpoint
CREATE TABLE `planning_revisions` (
	`environment` text NOT NULL,
	`revision` integer NOT NULL,
	`at` text NOT NULL,
	`actor` text NOT NULL,
	`summary` text NOT NULL,
	`payload` text NOT NULL,
	PRIMARY KEY(`environment`, `revision`)
);
--> statement-breakpoint
CREATE TABLE `planning_workers` (
	`environment` text NOT NULL,
	`id` text NOT NULL,
	`payload` text NOT NULL,
	PRIMARY KEY(`environment`, `id`)
);
