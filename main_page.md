/** @mainpage Sensor Data Acquisition Library

 *  @brief   Embedded C library for sensor drivers and real-time signal processing
 *
 *  @section overview Overview
 *
 *  This library provides a clean, portable API for interfacing with common
 *  sensor types and processing their data in real time on embedded targets.
 *
 *  @section modules API Modules
 *
 *  The library is organised into two top-level groups:
 *
 *  - @ref sensor_api      -- Sensor driver lifecycle, configuration, and I/O
 *  - @ref processor_api   -- Filtering, aggregation, and threshold detection
 *
 *  @section build Building
 *
 *  | Target       | Compiler              | Flags                            |
 *  |--------------|-----------------------|----------------------------------|
 *  | Host (test)  | gcc / clang           | `-std=c11 -Wall -Wextra -O2`    |
 *  | ARM Cortex-M | arm-none-eabi-gcc     | `-mcpu=cortex-m4 -std=c11 -Os`  |
 *  | ESP32        | xtensa-esp32-elf-gcc  | `-std=c11 -Os`                  |
 *
 *  @section example Quick Example
 *
 *  @code{.c}
 *  #include "sensor.h"
 *  #include "data_processor.h"
 *
 *  int main(void) {
 *      sensor_config_t scfg;
 *      sensor_default_config(SENSOR_TYPE_TEMPERATURE, &scfg);
 *      scfg.sample_rate_hz = 50;
 *
 *      sensor_driver_t *drv = sensor_create(&scfg);
 *      sensor_start(drv);
 *
 *      processor_config_t pcfg = {
 *          .filter_type  = FILTER_MOVING_AVG,
 *          .agg_mode     = AGG_MEAN,
 *          .filter_window = 8,
 *          .agg_window    = 10,
 *      };
 *      processor_t *proc = processor_create(&pcfg);
 *
 *      sensor_reading_t rd;
 *      for (int i = 0; i < 100; i++) {
 *          sensor_read(drv, &rd);
 *          processor_feed(proc, &rd);
 *      }
 *
 *      double out;
 *      processor_output(proc, &out);
 *
 *      processor_destroy(&proc);
 *      sensor_destroy(&drv);
 *      return 0;
 *  }
 *  @endcode
 *
 *  @section license License
 *
 *  MIT License -- see LICENSE file for details.
 */
