import * as Dialog from '@radix-ui/react-dialog';
import { add, format, isAfter, isBefore, isToday, startOfToday } from 'date-fns';
import scraped from '../../mocks/scraped.json';
import Schedule from './partials/Schedule/Schedule';
import { useEffect, useState } from 'react';

type Game = (typeof scraped)[number];

async function getSchedule(): Promise<Game[]> {
  console.log('FETCH');

  try {
    const response = await fetch('http://localhost:8000/schedule');
    return (await response.json()) as typeof scraped;
  } catch {
    return Promise.resolve([]);
  }
}

const HomeView = () => {
  const [schedule, setSchedule] = useState<Game[]>([]);

  useEffect(() => {
    const fetchSchedule = async () => {
      setSchedule(await getSchedule());
    };
    void fetchSchedule();
  }, []);

  console.log(schedule);

  const todayGames = schedule.filter((entry) => isToday(new Date(entry.datetime)));
  const soonGames = schedule.filter(
    (entry) =>
      isBefore(
        new Date(entry.datetime),
        add(startOfToday(), {
          years: 0,
          months: 1,
          weeks: 0,
          days: 0,
          hours: 0,
          minutes: 0,
          seconds: 0,
        }),
      ) && isAfter(new Date(entry.datetime), startOfToday()),
  );

  return (
    <div className="mx-auto h-full max-w-xl flex-col items-start">
      <Dialog.Root>
        <Dialog.Trigger>View full schedule</Dialog.Trigger>

        <Dialog.Content style={{ maxWidth: 450 }}>
          <Dialog.Title>
            <span>All games</span>
          </Dialog.Title>

          <Schedule games={schedule} />

          <div className="mt-4 justify-end gap-3">
            <Dialog.Close>Close</Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Root>

      <div className="flex-col items-start justify-center p-4">
        <p>
          <span>Today&lsquo;s game:&nbsp;</span>
          {todayGames.length === 0 ? (
            <span>no games today</span>
          ) : (
            todayGames.map((entry) => (
              <div key={entry.datetime}>
                <span>
                  on at {entry.location} at {format(new Date(entry.datetime), 'HH:mm')}
                </span>
              </div>
            ))
          )}
        </p>
      </div>

      <div className="w-full flex-col p-5">
        <p>Games in the next month:&nbsp;</p>
        <Schedule games={soonGames} />
      </div>
    </div>
  );
};

export default HomeView;
