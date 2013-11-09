#include <pebble.h>

static Window *window;
static TextLayer *time_layer;
static TextLayer *source_layer;
static TextLayer *message_layer;
static AppSync sync;
static uint8_t sync_buffer[124];
const int inbound_size = 124;
const int outbound_size = 124;

enum NotifyKey {
  SOURCE_KEY = 0x0,  // TUPLE_CSTRING
  MESSAGE_KEY = 0x1, // TUPLE_CSTRING
};

static void sync_error_callback(DictionaryResult dict_error, AppMessageResult app_message_error, void *context) {
  //APP_LOG(APP_LOG_LEVEL_DEBUG, "App Message Sync Error: %d", app_message_error);
}

static void sync_tuple_changed_callback(const uint32_t key, const Tuple* new_tuple, const Tuple* old_tuple, void* context) {
      //APP_LOG(APP_LOG_LEVEL_DEBUG, "Key: %lu", key);
      switch (key) {
        case SOURCE_KEY:
          //APP_LOG(APP_LOG_LEVEL_DEBUG, "Source: %s", new_tuple->value->cstring);
          text_layer_set_text(source_layer, new_tuple->value->cstring);
          layer_mark_dirty(text_layer_get_layer(source_layer));
          break;
        case MESSAGE_KEY:
          //APP_LOG(APP_LOG_LEVEL_DEBUG, "Message: %s", new_tuple->value->cstring);
          text_layer_set_text(message_layer, new_tuple->value->cstring);
          layer_mark_dirty(text_layer_get_layer(message_layer));
          break;
        
      }
}

 void out_sent_handler(DictionaryIterator *sent, void *context) {
   // outgoing message was delivered
 }


 void out_failed_handler(DictionaryIterator *failed, AppMessageResult reason, void *context) {
   // outgoing message failed
 }


 void in_received_handler(DictionaryIterator *received, void *context) {
   // incoming message received
 }


 void in_dropped_handler(AppMessageResult reason, void *context) {
   // incoming message dropped
 }

static void start_js(void) {
  Tuplet value = TupletInteger(2, 1);

  DictionaryIterator *iter;
  app_message_outbox_begin(&iter);

  if (iter == NULL) {
    return;
  }

  dict_write_tuplet(iter, &value);
  dict_write_end(iter);

  app_message_outbox_send();
}

static void select_click_handler(ClickRecognizerRef recognizer, void *context) {
}

static void up_click_handler(ClickRecognizerRef recognizer, void *context) {
}

static void down_click_handler(ClickRecognizerRef recognizer, void *context) {
}

static void click_config_provider(void *context) {
  window_single_click_subscribe(BUTTON_ID_SELECT, select_click_handler);
  window_single_click_subscribe(BUTTON_ID_UP, up_click_handler);
  window_single_click_subscribe(BUTTON_ID_DOWN, down_click_handler);
}

static void window_load(Window *window) {
  Layer *window_layer = window_get_root_layer(window);

  time_layer = text_layer_create(GRect(0, 5, 144, 68));
  text_layer_set_text_color(time_layer, GColorWhite);
  text_layer_set_background_color(time_layer, GColorClear);
  text_layer_set_font(time_layer, fonts_get_system_font(FONT_KEY_BITHAM_42_MEDIUM_NUMBERS));
  text_layer_set_text_alignment(time_layer, GTextAlignmentCenter);
  layer_add_child(window_layer, text_layer_get_layer(time_layer));

  source_layer = text_layer_create(GRect(0, 120, 144, 68));
  text_layer_set_text_color(source_layer, GColorWhite);
  text_layer_set_background_color(source_layer, GColorClear);
  text_layer_set_font(source_layer, fonts_get_system_font(FONT_KEY_GOTHIC_28_BOLD));
  text_layer_set_text_alignment(source_layer, GTextAlignmentCenter);
  layer_add_child(window_layer, text_layer_get_layer(source_layer));

  message_layer = text_layer_create(GRect(0, 65, 144, 68));
  text_layer_set_text_color(message_layer, GColorWhite);
  text_layer_set_background_color(message_layer, GColorClear);
  text_layer_set_font(message_layer, fonts_get_system_font(FONT_KEY_GOTHIC_24_BOLD));
  text_layer_set_text_alignment(message_layer, GTextAlignmentCenter);
  text_layer_set_overflow_mode(message_layer, GTextOverflowModeWordWrap);
  layer_add_child(window_layer, text_layer_get_layer(message_layer));

  if(bluetooth_connection_service_peek() == true){
      Tuplet initial_values[] = {
        TupletCString(SOURCE_KEY, "PbNotify"),
        TupletCString(MESSAGE_KEY, "No Messages"),
      };

      app_sync_init(&sync, sync_buffer, sizeof(sync_buffer),
                   initial_values, ARRAY_LENGTH(initial_values),
                   sync_tuple_changed_callback, sync_error_callback, NULL);

      start_js();
  }
  else {
    Tuplet initial_values[] = {
        TupletCString(SOURCE_KEY, "PbNotify"),
        TupletCString(MESSAGE_KEY, "Disconnected"),
      };

      app_sync_init(&sync, sync_buffer, sizeof(sync_buffer),
                   initial_values, ARRAY_LENGTH(initial_values),
                   sync_tuple_changed_callback, sync_error_callback, NULL);
  }

}

 static void handle_minute_tick(struct tm *tick_time, TimeUnits units_changed) {
      static char time_text[] = "00:00"; // Needs to be static because it's used by the system later.
      strftime(time_text, sizeof(time_text), "%I:%M", tick_time);
      text_layer_set_text(time_layer, time_text);
  }

 static void handle_bluetooth_toggle(bool connected) {
    //APP_LOG(APP_LOG_LEVEL_DEBUG, "Connected: %d", connected);
    if (connected == false){
      text_layer_set_text(message_layer, "Disconnected");
      layer_mark_dirty(text_layer_get_layer(message_layer));
      light_enable_interaction();
      vibes_short_pulse();
    }
    else {
      text_layer_set_text(message_layer, "Connection Restored");
      layer_mark_dirty(text_layer_get_layer(message_layer));
      light_enable_interaction();
      vibes_short_pulse();
      start_js();
    } 
  }

static void window_unload(Window *window) {
  app_sync_deinit(&sync);
  text_layer_destroy(source_layer);
  text_layer_destroy(message_layer);
}

static void init(void) {
  window = window_create();
  window_set_background_color(window, GColorBlack);
  window_set_fullscreen(window, true);
  window_set_click_config_provider(window, click_config_provider);
  window_set_window_handlers(window, (WindowHandlers) {
    .load = window_load,
    .unload = window_unload,
  });

  bluetooth_connection_service_subscribe(handle_bluetooth_toggle);

  app_message_register_inbox_received(in_received_handler);
  app_message_register_inbox_dropped(in_dropped_handler);
  app_message_register_outbox_sent(out_sent_handler);
  app_message_register_outbox_failed(out_failed_handler);
  app_message_open(inbound_size, outbound_size);

  tick_timer_service_subscribe(MINUTE_UNIT, handle_minute_tick);
  
  const bool animated = true;
  window_stack_push(window, animated);
}

static void deinit(void) {
  window_destroy(window);
}

int main(void) {
  init();

  APP_LOG(APP_LOG_LEVEL_DEBUG, "Done initializing, pushed window: %p", window);

  app_event_loop();
  deinit();
}
