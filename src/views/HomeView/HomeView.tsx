import { Flex } from '@radix-ui/themes';
import { isToday } from 'date-fns';
import schedule from '../../mocks/mock.json';

const HomeView = () => (
  <Flex height="100%" align="center" direction="column">
    <Flex asChild direction="column">
      <ol>
        {schedule.map(({ location, datetime }) => (
          <Flex asChild key={datetime}>
            <li>{isToday(new Date(datetime)) ? `there is a game today at ${location}` : ''}</li>
          </Flex>
        ))}
      </ol>
    </Flex>

    <Flex asChild direction="column">
      <ol>
        {schedule.map(({ location, datetime }) => (
          <Flex asChild key={datetime}>
            <li>
              {datetime} {location}
            </li>
          </Flex>
        ))}
      </ol>
    </Flex>
  </Flex>
);

export default HomeView;
