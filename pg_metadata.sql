drop table if exists public.source_system;
create table public.source_system
(
    source_system_id          varchar,
    lockbox_secret_id         varchar,
    source_system_desc        varchar,
    PRIMARY KEY (source_system_id)
);

insert into public.source_system(source_system_id, lockbox_secret_id, source_system_desc)
values ('000001', '<Идентификатор секрета LockBox>', 'Соединение SpeechSense 1');
insert into public.source_system(source_system_id, lockbox_secret_id, source_system_desc)
values ('000002', '<Идентификатор секрета LockBox>', 'Соединение SpeechSense 2');

drop table if exists public.talk;
create table public.talk
(
    id                        varchar,
    operator_name             varchar,
    operator_id               varchar,
    client_name               varchar,
    client_id                 varchar,
    "date"                    varchar,
    direction_outgoing        varchar,
    "language"                varchar,
    file_url                  varchar,
    additional_metadata       text,
    speechsense_talk_id       varchar,
    source_system_id          varchar,
    request_id                varchar,
    processed_dttm            varchar,
    metadata_file_path        varchar,
    PRIMARY KEY (id, source_system_id)
);

comment on column public.talk.id is 'Уникальный идентификатор входящей записи';
comment on column public.talk.additional_metadata is 'Необязательные поля метаданных в формате json-строки';
comment on column public.talk.speechsense_talk_id is 'Уникальный идентификатор диалога, присвоенный системой SpeechSense';
comment on column public.talk.source_system_id is 'Идентификатор системы-источника';
comment on column public.talk.request_id is 'Идентификтор вызова функции';
comment on column public.talk.processed_dttm is 'Дата и время вставки строки';
comment on column public.talk.metadata_file_path is 'Путь в бакете к файлу с метаданными';


drop table if exists public.errors;
create table public.errors
(
    metadata_file_path        varchar,
    error                     text,
    record                    text default '',
    request_id                varchar,
    processed_dttm            varchar,
    type                      varchar,
    PRIMARY KEY (metadata_file_path, record, request_id)
);

comment on column public.errors.metadata_file_path is 'Путь в бакете к файлу с метаданными';
comment on column public.errors.error is 'Сообщение об ошибке';
comment on column public.errors.record is 'Сериализованная запись метаданных';
comment on column public.errors.request_id is 'Идентификтор вызова функции';
comment on column public.errors.processed_dttm is 'Дата и время вставки строки';
comment on column public.errors.type is 'Тип ошибки';

